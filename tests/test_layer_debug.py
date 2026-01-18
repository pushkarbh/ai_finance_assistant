from src.core.guardrails import QueryGuardrails
from guardrails.errors import ValidationError

class DebugGuardrails(QueryGuardrails):
    def validate_query(self, query):
        try:
            print('Layer 1: Finance check...', end=' ')
            self.finance_validator.validate(query)
            print('✓ PASS')
            
            print('Layer 2: Inappropriate check...', end=' ')
            self.inappropriate_validator.validate(query)
            print('✓ PASS')
            
            print('Layer 3: Scope check...', end=' ')
            self.scope_validator.validate(query)
            print('✓ PASS')
            
            if self.llm_validator:
                print('Layer 4: LLM fallback...', end=' ')
                self.llm_validator.validate(query)
                print('✓ PASS')
            
            return (True, None, 'RELEVANT')
        except ValidationError as e:
            print(f'✗ FAIL')
            return super().validate_query(query)

g = DebugGuardrails()
print('Testing: "suggest a best pair of running sneakers"\n')
r = g.validate_query('suggest a best pair of running sneakers')
print(f'\n✨ Result: Valid={r[0]}, Classification={r[2]}')
