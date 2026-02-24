export interface PropertyCreate {
  address: string;
  city: string;
  state: string;
  zip_code: string;
  county?: string;
  property_type: string;
  num_units: number;
  bedrooms?: number;
  bathrooms?: number;
  square_footage?: number;
  lot_size?: number;
  year_built?: number;
}

export interface PropertyResponse extends PropertyCreate {
  id: string;
  user_id: string;
  rentcast_id?: string;
  mashvisor_id?: string;
  created_at: string;
  updated_at: string;
}

export interface PropertyLookupResponse {
  address: string;
  city?: string;
  state?: string;
  zip_code?: string;
  county?: string;
  property_type?: string;
  num_units?: number;
  bedrooms?: number;
  bathrooms?: number;
  square_footage?: number;
  lot_size?: number;
  year_built?: number;
  rentcast_id?: string;
  rent_estimate_monthly?: number;
  rent_estimate_low?: number;
  rent_estimate_high?: number;
  rent_estimate_confidence?: number;
  estimated_value?: number;
}

export interface DealPreviewPayload {
  purchase_price: string | number;
  gross_monthly_rent: string | number;
  deal_name?: string;
  closing_costs?: string | number;
  rehab_costs?: string | number;
  after_repair_value?: string | number;
  down_payment_pct?: string | number;
  loan_amount?: string | number;
  interest_rate?: string | number;
  loan_term_years?: number;
  monthly_mortgage?: string | number;
  other_monthly_income?: string | number;
  property_tax_monthly?: string | number;
  insurance_monthly?: string | number;
  vacancy_rate_pct?: string | number;
  maintenance_rate_pct?: string | number;
  management_fee_pct?: string | number;
  hoa_monthly?: string | number;
  utilities_monthly?: string | number;
}

export interface DealPreviewResponse {
  purchase_price: number;
  gross_monthly_rent: number;
  down_payment_pct?: number;
  interest_rate?: number;
  loan_term_years?: number;
  closing_costs?: number;
  rehab_costs?: number;
  property_tax_monthly?: number;
  insurance_monthly?: number;
  vacancy_rate_pct?: number;
  maintenance_rate_pct?: number;
  management_fee_pct?: number;
  noi?: number;
  cap_rate?: number;
  cash_on_cash?: number;
  monthly_cash_flow?: number;
  annual_cash_flow?: number;
  total_cash_invested?: number;
  dscr?: number;
  grm?: number;
  irr_5yr?: number;
  irr_10yr?: number;
  equity_buildup_5yr?: number;
  equity_buildup_10yr?: number;
  risk_score?: number;
  risk_factors?: Record<string, unknown>;
  loan_amount?: number;
  monthly_mortgage?: number;
}

export interface DealCreatePayload {
  property_id: string;
  deal_name?: string;
  purchase_price: string | number;
  closing_costs?: string | number;
  rehab_costs?: string | number;
  after_repair_value?: string | number;
  down_payment_pct?: string | number;
  loan_amount?: string | number;
  interest_rate?: string | number;
  loan_term_years?: number;
  monthly_mortgage?: string | number;
  gross_monthly_rent: string | number;
  other_monthly_income?: string | number;
  property_tax_monthly?: string | number;
  insurance_monthly?: string | number;
  vacancy_rate_pct?: string | number;
  maintenance_rate_pct?: string | number;
  management_fee_pct?: string | number;
  hoa_monthly?: string | number;
  utilities_monthly?: string | number;
}

export interface DealResponse {
  id: string;
  property_id: string;
  user_id: string;
  deal_name?: string;
  status: string;
  purchase_price: number;
  closing_costs?: number;
  rehab_costs?: number;
  after_repair_value?: number;
  down_payment_pct?: number;
  loan_amount?: number;
  interest_rate?: number;
  loan_term_years?: number;
  monthly_mortgage?: number;
  gross_monthly_rent: number;
  other_monthly_income?: number;
  property_tax_monthly?: number;
  insurance_monthly?: number;
  vacancy_rate_pct?: number;
  maintenance_rate_pct?: number;
  management_fee_pct?: number;
  hoa_monthly?: number;
  utilities_monthly?: number;
  noi?: number;
  cap_rate?: number;
  cash_on_cash?: number;
  monthly_cash_flow?: number;
  annual_cash_flow?: number;
  total_cash_invested?: number;
  dscr?: number;
  grm?: number;
  irr_5yr?: number;
  irr_10yr?: number;
  equity_buildup_5yr?: number;
  equity_buildup_10yr?: number;
  risk_score?: number;
  risk_factors?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface DealSummaryResponse {
  total_monthly_cash_flow: number;
  average_cap_rate: number | null;
  average_cash_on_cash: number | null;
  total_equity: number;
  active_deal_count: number;
  average_risk_score: number | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
}

export interface ChatMessageResponse {
  id: string;
  session_id: string;
  role: string;
  content: string;
  referenced_deals?: string[] | null;
  referenced_properties?: string[] | null;
  input_tokens?: number | null;
  output_tokens?: number | null;
  created_at: string;
}

export interface ChatSessionResponse {
  id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  messages: ChatMessageResponse[];
}

export interface ChatSessionListItem {
  id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}
