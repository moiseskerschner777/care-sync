export const OPERATION_LABELS: Record<string, string> = {
  validate_coverage: 'Validate Coverage',
  create_exam: 'Create Exam',
};

export const ORIGIN_LABELS: Record<string, string> = {
  ORIGIN_A: 'Bug or data issue in LabCore',
  ORIGIN_B: 'External system rejected the request',
  CONTRACT: 'Business rule / contract violation',
  INFRA: 'Network or system failure',
  AMBIGUOUS: 'Not enough evidence (confidence < 0.70)',
};

export function operationLabel(key: string): string {
  return OPERATION_LABELS[key] ?? key;
}

export function originLabel(key: string): string {
  return ORIGIN_LABELS[key] ?? key;
}
