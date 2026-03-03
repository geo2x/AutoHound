# AutoHound Test Data

This folder contains sample BloodHound data for testing AutoHound's attack path analysis capabilities.

## 📁 Files

- **sample1_kerberoasting.json** - CORP.LOCAL domain with Kerberoasting and ACL abuse vectors
- **sample2_delegation.json** - CONTOSO.COM domain with delegation-based attack paths
- **sample3_acl_abuse.json** - MEGACORP.NET domain with complex ACL chains and GPO abuse
- **HOW_TO_TEST.txt** - Comprehensive testing guide with examples
- **AUTOHOUND_HELP.txt** - Complete CLI help output reference

## 🚀 Quick Test

```bash
cd test_data
autohound -i sample1_kerberoasting.json -o ./reports
```

See **HOW_TO_TEST.txt** for detailed instructions and all testing scenarios.

## 📊 Sample Data Details

### Sample 1: Kerberoasting (CORP.LOCAL)
- 9 objects (users, groups, computers)
- Attack vectors: SPN-based attacks, GenericAll, WriteDacl, ForceChangePassword
- Difficulty: ⭐⭐ (Easy-Medium)

### Sample 2: Delegation (CONTOSO.COM)
- 9 objects
- Attack vectors: Unconstrained delegation, constrained delegation, RBCD
- Difficulty: ⭐⭐⭐ (Medium-Hard)

### Sample 3: ACL Abuse (MEGACORP.NET)
- 12 objects including GPO
- Attack vectors: Complex ACL chains, DCSync rights, GPO modification
- Difficulty: ⭐⭐⭐⭐ (Hard)

## ⚠️ Legal Notice

These are synthetic test datasets for authorized security testing only. Use AutoHound only on systems you own or have explicit written permission to test.

---
© 2026 ACH Research Division
