export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Tier = 'free' | 'starter' | 'pro';

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          email: string | null;
          credits: number;
          tier: Tier;
          billing_key: string | null;
          customer_key: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id: string;
          email?: string | null;
          credits?: number;
          tier?: Tier;
          billing_key?: string | null;
          customer_key?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          email?: string | null;
          credits?: number;
          tier?: Tier;
          billing_key?: string | null;
          customer_key?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      generation_logs: {
        Row: {
          id: string;
          user_id: string;
          product_name: string;
          selling_points: string | null;
          tone: string;
          script_content: Json | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          product_name: string;
          selling_points?: string | null;
          tone: string;
          script_content?: Json | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          product_name?: string;
          selling_points?: string | null;
          tone?: string;
          script_content?: Json | null;
          created_at?: string;
        };
        Relationships: [];
      };
      billing_events: {
        Row: {
          id: string;
          user_id: string | null;
          order_id: string | null;
          status: string;
          amount: number | null;
          raw_payload: Json | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id?: string | null;
          order_id?: string | null;
          status: string;
          amount?: number | null;
          raw_payload?: Json | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string | null;
          order_id?: string | null;
          status?: string;
          amount?: number | null;
          raw_payload?: Json | null;
          created_at?: string;
        };
        Relationships: [];
      };
    };
    Views: Record<string, never>;
    Functions: {
      deduct_user_credits: {
        Args: { p_user_id: string; p_amount?: number };
        Returns: number;
      };
      add_user_credits: {
        Args: { p_user_id: string; p_amount: number; p_tier?: string | null };
        Returns: number;
      };
    };
    Enums: Record<string, never>;
    CompositeTypes: Record<string, never>;
  };
}
