export function scoreBadge(score) {
  if (score >= 80) return 'Strong Match'
  if (score >= 60) return 'Good Match'
  return 'Weak Match'
}
