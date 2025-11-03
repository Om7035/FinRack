"""Agent orchestrator for routing and collaboration"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent
from app.services.llm_service import llm_service
import logging
import re

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrate multiple agents for complex tasks"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize orchestrator
        
        Args:
            db: Database session
        """
        self.db = db
        self.agents: Dict[str, BaseAgent] = {}
        
        # Intent patterns for routing
        self.intent_patterns = {
            'budget': ['budget', 'spending', 'expense', 'money spent'],
            'fraud': ['fraud', 'suspicious', 'unusual', 'anomaly', 'security'],
            'goal': ['goal', 'save', 'saving', 'target', 'milestone'],
            'investment': ['invest', 'portfolio', 'stock', 'asset', 'allocation'],
            'general': ['help', 'what', 'how', 'explain', 'show me'],
        }
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent
        
        Args:
            agent: Agent instance
        """
        self.agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")
    
    async def route_task(
        self,
        user_input: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Route task to appropriate agent
        
        Args:
            user_input: User input/query
            user_id: User ID
            context: Additional context
            
        Returns:
            Task result
        """
        # Classify intent
        intent = await self._classify_intent(user_input)
        
        logger.info(f"Classified intent: {intent}")
        
        # Route to appropriate agent
        agent_name = self._get_agent_for_intent(intent)
        
        if agent_name and agent_name in self.agents:
            agent = self.agents[agent_name]
            
            result = await agent.execute(
                task_type=intent,
                input_data={
                    'query': user_input,
                    'context': context or {},
                },
                user_id=user_id,
            )
            
            return {
                'agent': agent_name,
                'intent': intent,
                'result': result,
            }
        else:
            # Fallback to concierge agent
            if 'finance_concierge' in self.agents:
                agent = self.agents['finance_concierge']
                result = await agent.execute(
                    task_type='general_query',
                    input_data={'query': user_input, 'context': context or {}},
                    user_id=user_id,
                )
                return {
                    'agent': 'finance_concierge',
                    'intent': 'general',
                    'result': result,
                }
            
            return {
                'agent': None,
                'intent': intent,
                'result': {'error': 'No suitable agent found'},
            }
    
    async def _classify_intent(self, user_input: str) -> str:
        """
        Classify user intent
        
        Args:
            user_input: User input
            
        Returns:
            Intent classification
        """
        user_input_lower = user_input.lower()
        
        # Rule-based classification
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in user_input_lower for pattern in patterns):
                return intent
        
        # Fallback to LLM classification
        try:
            prompt = f"""Classify the following user query into one of these categories:
- budget: Questions about budgets, spending, expenses
- fraud: Questions about fraud, suspicious activity, security
- goal: Questions about financial goals, savings targets
- investment: Questions about investments, portfolio, stocks
- general: General financial questions

User query: "{user_input}"

Respond with only the category name."""
            
            classification = await llm_service.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=10,
            )
            
            classification = classification.strip().lower()
            if classification in self.intent_patterns:
                return classification
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
        
        return 'general'
    
    def _get_agent_for_intent(self, intent: str) -> Optional[str]:
        """
        Get agent name for intent
        
        Args:
            intent: Intent classification
            
        Returns:
            Agent name
        """
        intent_to_agent = {
            'budget': 'budget_guardian',
            'fraud': 'fraud_sentinel',
            'goal': 'wealth_planner',
            'investment': 'investment_advisor',
            'general': 'finance_concierge',
        }
        
        return intent_to_agent.get(intent)
    
    async def execute_workflow(
        self,
        workflow_steps: List[Dict[str, Any]],
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Execute multi-agent workflow
        
        Args:
            workflow_steps: List of workflow steps
            user_id: User ID
            
        Returns:
            List of step results
        """
        results = []
        context = {}
        
        for step in workflow_steps:
            agent_name = step.get('agent')
            task_type = step.get('task_type')
            input_data = step.get('input_data', {})
            
            # Add previous results to context
            input_data['context'] = context
            
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                
                result = await agent.execute(
                    task_type=task_type,
                    input_data=input_data,
                    user_id=user_id,
                )
                
                results.append({
                    'step': len(results) + 1,
                    'agent': agent_name,
                    'result': result,
                })
                
                # Update context with result
                context[f"step_{len(results)}"] = result
            else:
                results.append({
                    'step': len(results) + 1,
                    'agent': agent_name,
                    'error': 'Agent not found',
                })
        
        return results
    
    async def collaborate(
        self,
        task: str,
        user_id: str,
        agents: List[str],
    ) -> Dict[str, Any]:
        """
        Have multiple agents collaborate on a task
        
        Args:
            task: Task description
            user_id: User ID
            agents: List of agent names to involve
            
        Returns:
            Collaboration result
        """
        results = {}
        
        for agent_name in agents:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                
                try:
                    result = await agent.execute(
                        task_type='collaborate',
                        input_data={
                            'task': task,
                            'other_agents': [a for a in agents if a != agent_name],
                        },
                        user_id=user_id,
                    )
                    
                    results[agent_name] = result
                except Exception as e:
                    logger.error(f"Agent {agent_name} collaboration failed: {e}")
                    results[agent_name] = {'error': str(e)}
        
        # Synthesize results
        synthesis = await self._synthesize_results(task, results)
        
        return {
            'task': task,
            'agents': agents,
            'individual_results': results,
            'synthesis': synthesis,
        }
    
    async def _synthesize_results(
        self,
        task: str,
        results: Dict[str, Any],
    ) -> str:
        """
        Synthesize results from multiple agents
        
        Args:
            task: Original task
            results: Results from agents
            
        Returns:
            Synthesized response
        """
        results_str = "\n\n".join([
            f"{agent}: {result}"
            for agent, result in results.items()
        ])
        
        prompt = f"""Task: {task}

Results from different agents:
{results_str}

Synthesize these results into a coherent, actionable response for the user."""
        
        try:
            synthesis = await llm_service.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=500,
            )
            return synthesis
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return "Multiple agents provided insights. Please review individual results."
