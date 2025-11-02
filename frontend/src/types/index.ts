export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  is_2fa_enabled: boolean;
  created_at: string;
}

export interface UserWithProfile extends User {
  full_name?: string;
  phone_number?: string;
  timezone: string;
  currency: string;
}

export interface BankAccount {
  id: string;
  user_id: string;
  name: string;
  account_type: string;
  current_balance: number;
  currency: string;
  mask?: string;
  is_active: boolean;
  last_synced?: string;
}

export interface Transaction {
  id: string;
  account_id: string;
  amount: number;
  date: string;
  name: string;
  merchant_name?: string;
  category?: string;
  notes?: string;
}

export interface Budget {
  id: string;
  user_id: string;
  name: string;
  category: string;
  amount: number;
  period: 'weekly' | 'monthly' | 'yearly';
  start_date: string;
  is_active: boolean;
}

export interface FinancialGoal {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  target_amount: number;
  current_amount: number;
  deadline?: string;
  priority: 'low' | 'medium' | 'high';
  status: 'in_progress' | 'achieved' | 'abandoned';
}
