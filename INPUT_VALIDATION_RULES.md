# ✅ Input Validation Standards & Rules

**Complete validation guide for all API endpoints**

---

## 🎯 Validation Philosophy

```
Input Validation Hierarchy:
┌─────────────────────────────────────────┐
│ 1. CLIENT-SIDE VALIDATION               │
│    (Quick feedback, UX improvement)     │
│                                          │
│ 2. API-LEVEL VALIDATION                 │
│    (Format, type, length checks)        │
│                                          │
│ 3. BUSINESS-LOGIC VALIDATION            │
│    (Duplicate, conflicts, rules)        │
│                                          │
│ 4. DATABASE-LEVEL VALIDATION            │
│    (Constraints, triggers)              │
│                                          │
│ 5. SECURITY VALIDATION                  │
│    (SQL injection, XSS, auth)           │
└─────────────────────────────────────────┘

Rule: NEVER trust user input. ALWAYS validate on server.
```

---

## 📐 Standard Validation Rules

### String Validation

```python
def validate_string(value, min_len=1, max_len=255, regex=None):
    """
    Validate string input
    
    Args:
        value: String to validate
        min_len: Minimum length (default: 1)
        max_len: Maximum length (default: 255)
        regex: Optional regex pattern to match
    
    Returns:
        (is_valid, error_message)
    """
    # Check type
    if not isinstance(value, str):
        return False, "Must be a string"
    
    # Check length
    if len(value.strip()) < min_len:
        return False, f"Minimum {min_len} characters required"
    
    if len(value) > max_len:
        return False, f"Maximum {max_len} characters allowed"
    
    # Check regex pattern
    if regex:
        import re
        if not re.match(regex, value):
            return False, f"Invalid format"
    
    return True, None

# Examples:
validate_string("KALYAN", min_len=3, max_len=50)  # ✅ True
validate_string("", min_len=1)  # ❌ False - too short
validate_string("A" * 300, max_len=255)  # ❌ False - too long
```

### Number Validation

```python
def validate_number(value, min_val=None, max_val=None, is_integer=False):
    """Validate numeric input"""
    try:
        num = float(value) if not is_integer else int(value)
    except (ValueError, TypeError):
        return False, "Must be a valid number"
    
    if min_val is not None and num < min_val:
        return False, f"Minimum value: {min_val}"
    
    if max_val is not None and num > max_val:
        return False, f"Maximum value: {max_val}"
    
    return True, None

# Examples:
validate_number(500, min_val=100, max_val=50000)  # ✅ True
validate_number(-100, min_val=0)  # ❌ False - below minimum
validate_number(999999, max_val=50000)  # ❌ False - above maximum
```

### Email Validation

```python
import re

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, None
    return False, "Invalid email format"

# Examples:
validate_email("user@example.com")  # ✅ True
validate_email("user@")  # ❌ False - invalid format
```

### Phone Validation

```python
def validate_phone(phone):
    """Validate Indian phone number"""
    # Remove spaces and special chars
    phone = re.sub(r'\D', '', str(phone))
    
    # Check length (10 digits for India)
    if len(phone) != 10:
        return False, "Phone must be 10 digits"
    
    # Check first digit (should be 6-9)
    if phone[0] not in '6789':
        return False, "Invalid phone number"
    
    return True, None

# Examples:
validate_phone("9876543210")  # ✅ True
validate_phone("1234567890")  # ❌ False - starts with 1
validate_phone("987654321")   # ❌ False - only 9 digits
```

### UPI ID Validation

```python
def validate_upi(upi_id):
    """Validate UPI ID format"""
    pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z]{3,}$'
    if not re.match(pattern, upi_id):
        return False, "Invalid UPI format (e.g., user@upi)"
    return True, None

# Examples:
validate_upi("user@upi")  # ✅ True
validate_upi("user@bank")  # ✅ True
validate_upi("invalid")   # ❌ False
```

### UTR Validation

```python
def validate_utr(utr):
    """Validate UTR/Reference number"""
    # Remove spaces
    utr = str(utr).strip().upper()
    
    # Length check (usually 8-20 chars)
    if len(utr) < 8 or len(utr) > 20:
        return False, "UTR must be 8-20 characters"
    
    # Allow alphanumeric
    if not re.match(r'^[A-Z0-9]+$', utr):
        return False, "UTR can only contain letters and numbers"
    
    return True, None

# Examples:
validate_utr("405070123456")  # ✅ True
validate_utr("invalid!@#")    # ❌ False - special chars
validate_utr("1234")          # ❌ False - too short
```

---

## 💳 Payment Validation

### Deposit Amount

```python
def validate_deposit_amount(amount):
    """Validate deposit amount"""
    MIN_DEPOSIT = 100
    MAX_DEPOSIT = 50000
    
    # Parse to number
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return False, "Amount must be a number"
    
    # Check range
    if amount < MIN_DEPOSIT:
        return False, f"Minimum deposit: ₹{MIN_DEPOSIT}"
    
    if amount > MAX_DEPOSIT:
        return False, f"Maximum deposit: ₹{MAX_DEPOSIT}"
    
    # Check decimal places (max 2)
    if amount != round(amount, 2):
        return False, "Maximum 2 decimal places allowed"
    
    return True, None

# Examples:
validate_deposit_amount(500)     # ✅ True
validate_deposit_amount(50)      # ❌ False - below minimum
validate_deposit_amount(100000)  # ❌ False - above maximum
```

### Withdrawal Amount

```python
def validate_withdrawal_amount(amount, available_balance):
    """Validate withdrawal amount"""
    MIN_WITHDRAWAL = 100
    MAX_WITHDRAWAL = 30000
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return False, "Amount must be a number"
    
    # Check range
    if amount < MIN_WITHDRAWAL:
        return False, f"Minimum withdrawal: ₹{MIN_WITHDRAWAL}"
    
    if amount > MAX_WITHDRAWAL:
        return False, f"Maximum withdrawal: ₹{MAX_WITHDRAWAL}"
    
    # Check balance
    if amount > available_balance:
        return False, f"Insufficient balance. Available: ₹{available_balance}"
    
    return True, None
```

---

## 📝 Entry Validation

### Market Name

```python
def validate_market_name(market):
    """Validate market name"""
    if not isinstance(market, str):
        return False, "Market must be text"
    
    market = market.strip().upper()
    
    # Length
    if len(market) < 3 or len(market) > 50:
        return False, "Market name: 3-50 characters"
    
    # Only alphanumeric and spaces
    if not re.match(r'^[A-Z0-9\s]+$', market):
        return False, "Only letters, numbers and spaces allowed"
    
    return True, market  # Return normalized value

# Examples:
validate_market_name("kalyan")  # ✅ ("kalyan", None) → normalized
validate_market_name("sridevi day")  # ✅ ("SRIDEVI DAY", None)
validate_market_name("***invalid***")  # ❌ False
```

### Game Type

```python
def validate_game_type(game_type):
    """Validate game type"""
    VALID_TYPES = ["ANK", "JODI", "PENEL"]
    
    game_type = str(game_type).strip().upper()
    
    if game_type not in VALID_TYPES:
        return False, f"Must be one of: {', '.join(VALID_TYPES)}"
    
    return True, game_type

# Examples:
validate_game_type("ank")  # ✅ ("ANK", None)
validate_game_type("jodi")  # ✅ ("JODI", None)
validate_game_type("invalid")  # ❌ False
```

### Digits

```python
def validate_digits(digits, game_type):
    """Validate game digits"""
    try:
        # Parse digits (can be list or comma-separated string)
        if isinstance(digits, str):
            digit_list = [d.strip() for d in digits.split(',')]
        else:
            digit_list = list(digits)
        
        digit_list = [str(d).strip() for d in digit_list]
        
        # Check count based on game type
        if game_type == "ANK" and len(digit_list) != 1:
            return False, "ANK must have exactly 1 digit"
        
        if game_type == "JODI" and len(digit_list) != 2:
            return False, "JODI must have exactly 2 digits"
        
        if game_type == "PENEL" and len(digit_list) != 3:
            return False, "PENEL must have exactly 3 digits"
        
        # Each digit 0-9
        for digit in digit_list:
            if not re.match(r'^[0-9]$', digit):
                return False, f"Invalid digit: {digit}"
        
        return True, digit_list
        
    except Exception as e:
        return False, f"Invalid digits format"

# Examples:
validate_digits("5", "ANK")  # ✅ (["5"], None)
validate_digits("5,7", "JODI")  # ✅ (["5", "7"], None)
validate_digits("5,7,9", "PENEL")  # ✅ (["5", "7", "9"], None)
validate_digits("5,7", "ANK")  # ❌ False - wrong count
```

---

## 🔐 Security Validation

### SQL Injection Prevention

```python
def validate_against_sql_injection(value):
    """Check for SQL injection patterns"""
    dangerous_patterns = [
        r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)",
        r"(--|;|\'|\"|\*)",
        r"(\bOR\b.*=.*)",
    ]
    
    value_upper = str(value).upper()
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value_upper):
            return False, "Invalid characters detected"
    
    return True, None
```

### XSS Prevention

```python
def sanitize_string(value):
    """Remove XSS attack vectors"""
    dangerous_chars = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '&': '&amp;'
    }
    
    result = str(value)
    for char, safe in dangerous_chars.items():
        result = result.replace(char, safe)
    
    return result

# Example:
sanitize_string("<script>alert('xss')</script>")
# Returns: "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
```

---

## 📋 Complete Validation Checklist

### For Every API Endpoint:

```
✅ Input Type Validation
   - Is it the correct data type?
   - String? Number? Array?

✅ Format Validation
   - Correct format (email, phone, UPI)?
   - Regex patterns match?

✅ Length/Range Validation
   - Minimum length/value?
   - Maximum length/value?

✅ Business Logic Validation
   - Duplicate check?
   - Balance sufficient?
   - Market exists?

✅ Security Validation
   - SQL injection patterns?
   - XSS vectors?
   - Authorization check?

✅ Error Messages
   - User-friendly?
   - Specific issue described?
   - Clear action required?
```

---

## 🔄 Validation Workflow Example

```python
@app.route('/api/submit/payment', methods=['POST'])
def submit_payment():
    """Complete validation example"""
    
    data = request.get_json()
    
    # 1. Check JSON
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # 2. Validate each field
    errors = {}
    
    # Validate amount
    valid, msg = validate_deposit_amount(data.get('amount'))
    if not valid:
        errors['amount'] = msg
    
    # Validate UTR
    valid, msg = validate_utr(data.get('utr'))
    if not valid:
        errors['utr'] = msg
    
    # Validate UPI/Bank
    if data.get('method') == 'upi':
        valid, msg = validate_upi(data.get('upiId'))
        if not valid:
            errors['upiId'] = msg
    
    # Check for errors
    if errors:
        return jsonify({
            'status': 'error',
            'errors': errors
        }), 400
    
    # 3. Check duplicate UTR
    if payment_exists_with_utr(data['utr']):
        return jsonify({
            'error': 'This UTR already used in last 24 hours'
        }), 400
    
    # 4. Check business logic
    user = get_user(data['userId'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user.get('kyc_verified'):
        return jsonify({'error': 'KYC not verified'}), 403
    
    # 5. All checks passed - proceed
    payment = create_payment(data)
    return jsonify({
        'status': 'success',
        'paymentId': payment['id']
    }), 201
```

---

## 📚 Validation Error Codes

| Code | Message | Status |
|------|---------|--------|
| INVALID_TYPE | Wrong data type | 400 |
| INVALID_FORMAT | Format mismatch | 400 |
| TOO_SHORT | String too short | 400 |
| TOO_LONG | String too long | 400 |
| OUT_OF_RANGE | Value out of range | 400 |
| DUPLICATE | Already exists | 409 |
| NOT_FOUND | Resource not found | 404 |
| INSUFFICIENT_BALANCE | Not enough balance | 400 |
| UNAUTHORIZED | Not authorized | 403 |
| SERVER_ERROR | Internal error | 500 |

---

## 🚀 Implementation Checklist

- [ ] Import validation utilities in all files
- [ ] Add validators to all API endpoints
- [ ] Test with invalid inputs
- [ ] Test with edge cases
- [ ] Document validation rules
- [ ] Add to code review checklist
- [ ] Monitor validation errors in logs
- [ ] Update validation rules as needed

---

## 📞 Support

For validation questions or to report bypasses:
- Check this document first
- Review code examples
- Ask in tech team meeting
- Create GitHub issue if bug found
