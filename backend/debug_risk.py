from app import analyze_password_patterns

email = "poojitha.bonela_2027@woxsen.edu.in"
# test a password that should be high risk
p = "Password123!"

patterns, risk = analyze_password_patterns(p, email)
print(f"EMAIL: {email}")
print(f"PASS : {p}")
print(f"RISK : {risk}")
print(f"PATT : {patterns}")
