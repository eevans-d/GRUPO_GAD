#!/usr/bin/env python3
"""
Code Review Analysis Tool for v1.3.0
Analyzes commits: dfa9004, d65b1c2, 9d2c80b
"""

import subprocess
import json
from typing import Dict, List
from datetime import datetime


class CodeReviewAnalyzer:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.findings = {
            "dfa9004": [],
            "d65b1c2": [],
            "9d2c80b": []
        }
        self.scores = {}

    def run_command(self, cmd: str) -> str:
        """Execute shell command and return output"""
        result = subprocess.run(
            cmd, shell=True, cwd=self.repo_path,
            capture_output=True, text=True
        )
        return result.stdout + result.stderr

    def analyze_commit(self, commit_sha: str, files_changed: List[str]):
        """Analyze a specific commit"""
        print(f"\n📋 Analyzing commit: {commit_sha}")
        
        findings = []
        
        # Get commit diff
        diff = self.run_command(f"git show {commit_sha}")
        
        # Analyze each file
        for file in files_changed:
            print(f"   Checking: {file}")
            
            # Check for security issues
            if "secrets" in file or "password" in file or "token" in file:
                if any(word in diff for word in ["SECRET", "PASSWORD", "API_KEY"]):
                    findings.append({
                        "severity": "CRITICAL",
                        "type": "Security",
                        "file": file,
                        "message": "Potential hardcoded secret detected"
                    })
            
            # Check for proper error handling
            if ".py" in file:
                if "except:" in diff and "except Exception" not in diff:
                    findings.append({
                        "severity": "WARNING",
                        "type": "Error Handling",
                        "file": file,
                        "message": "Bare except clause detected - use specific exceptions"
                    })
            
            # Check for TODO/FIXME
            if "TODO" in diff or "FIXME" in diff:
                findings.append({
                    "severity": "INFO",
                    "type": "Code Quality",
                    "file": file,
                    "message": "TODO or FIXME comment found - address before merge"
                })
            
            # Check for console logs in production code
            if ".py" in file and "print(" in diff:
                findings.append({
                    "severity": "WARNING",
                    "type": "Code Quality",
                    "file": file,
                    "message": "Print statement detected - use logging instead"
                })
        
        self.findings[commit_sha] = findings
        return findings

    def analyze_commit_dfa9004(self):
        """Detailed analysis of DB mapping fixes"""
        print("\n" + "="*60)
        print("Commit dfa9004: Fix DB Field Mappings")
        print("="*60)
        
        files = ["src/api/routers/telegram_auth.py", "src/api/routers/telegram_tasks.py"]
        findings = self.analyze_commit("dfa9004", files)
        
        # Specific checks for this commit
        score = 100
        
        # Check telegram_auth.py
        auth_content = self.run_command("git show dfa9004:src/api/routers/telegram_auth.py")
        
        checks = {
            "Usuario import present": "from src.db.models import Usuario" in auth_content or "import Usuario" in auth_content,
            "No 'User' model reference": "User" not in auth_content or "# User" in auth_content,
            "SECRET_KEY usage correct": "settings.SECRET_KEY" in auth_content,
            "JWT logic intact": "create_access_token" in auth_content
        }
        
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                score -= 20
                findings.append({
                    "severity": "CRITICAL",
                    "type": "Implementation",
                    "message": f"Check failed: {check_name}"
                })
        
        self.scores["dfa9004"] = score
        print(f"\n  Score: {score}/100")
        return findings

    def analyze_commit_d65b1c2(self):
        """Detailed analysis of User Management"""
        print("\n" + "="*60)
        print("Commit d65b1c2: ME4 User Management Interface")
        print("="*60)
        
        files = [
            "src/api/routers/usuarios.py",
            "dashboard/static/js/users_management.js",
            "dashboard/static/css/users_management.css"
        ]
        findings = self.analyze_commit("d65b1c2", files)
        
        score = 100
        
        # Check usuarios.py
        usuarios_content = self.run_command("git show d65b1c2:src/api/routers/usuarios.py")
        
        api_checks = {
            "@router.get()": "@router.get()" in usuarios_content,
            "@router.post()": "@router.post()" in usuarios_content,
            "@router.put()": "@router.put()" in usuarios_content,
            "@router.delete()": "@router.delete()" in usuarios_content,
            "Input validation": "telegram_id" in usuarios_content and "nivel" in usuarios_content,
            "Error handling": "404" in usuarios_content or "HTTPException" in usuarios_content,
            "Pagination support": "skip" in usuarios_content and "limit" in usuarios_content
        }
        
        print("\n  API Endpoints:")
        for check_name, passed in api_checks.items():
            status = "✅" if passed else "❌"
            print(f"    {status} {check_name}")
            if not passed:
                score -= 10
        
        # Check JavaScript
        print("\n  Frontend:")
        js_content = self.run_command("git show d65b1c2:dashboard/static/js/users_management.js")
        
        js_checks = {
            "CRUD methods": all(method in js_content for method in ["loadUsers", "saveUser", "deleteUser"]),
            "XSS prevention": "escapeHtml" in js_content,
            "Form validation": "validate" in js_content or "validation" in js_content,
            "Error handling": "catch" in js_content or "error" in js_content
        }
        
        for check_name, passed in js_checks.items():
            status = "✅" if passed else "❌"
            print(f"    {status} {check_name}")
            if not passed:
                score -= 15
        
        self.scores["d65b1c2"] = score
        print(f"\n  Score: {score}/100")
        return findings

    def analyze_commit_9d2c80b(self):
        """Detailed analysis of Cache System"""
        print("\n" + "="*60)
        print("Commit 9d2c80b: ME5 Redis Cache System")
        print("="*60)
        
        files = ["src/core/cache_decorators.py", "src/api/routers/usuarios.py"]
        findings = self.analyze_commit("9d2c80b", files)
        
        score = 100
        
        # Check cache decorators
        cache_content = self.run_command("git show 9d2c80b:src/core/cache_decorators.py")
        
        cache_checks = {
            "@cache_result decorator": "@cache_result" in cache_content,
            "@cache_and_invalidate decorator": "@cache_and_invalidate" in cache_content,
            "TTL support": "ttl" in cache_content or "TTL" in cache_content,
            "Redis integration": "redis" in cache_content or "Redis" in cache_content,
            "Key generation": "key" in cache_content or "cache_key" in cache_content,
            "Error handling": "except" in cache_content
        }
        
        print("\n  Cache Implementation:")
        for check_name, passed in cache_checks.items():
            status = "✅" if passed else "❌"
            print(f"    {status} {check_name}")
            if not passed:
                score -= 12
        
        # Check integration in usuarios.py
        print("\n  Integration in usuarios.py:")
        usuarios_content = self.run_command("git show 9d2c80b:src/api/routers/usuarios.py")
        
        integration_checks = {
            "GET endpoints cached": "@cache_result" in usuarios_content,
            "Invalidation on POST": "@cache_and_invalidate" in usuarios_content,
            "Invalidation on PUT": "@cache_and_invalidate" in usuarios_content,
            "Invalidation on DELETE": "@cache_and_invalidate" in usuarios_content
        }
        
        for check_name, passed in integration_checks.items():
            status = "✅" if passed else "❌"
            print(f"    {status} {check_name}")
            if not passed:
                score -= 15
        
        self.scores["9d2c80b"] = score
        print(f"\n  Score: {score}/100")
        return findings

    def generate_report(self):
        """Generate final review report"""
        print("\n" + "="*60)
        print("📊 CODE REVIEW SUMMARY")
        print("="*60)
        
        print("\nCommit Scores:")
        total_score = 0
        for commit_sha, score in self.scores.items():
            status = "✅ PASS" if score >= 90 else "⚠️  REVIEW" if score >= 75 else "❌ FAIL"
            print(f"  {commit_sha}: {score}/100 {status}")
            total_score += score
        
        avg_score = total_score / len(self.scores) if self.scores else 0
        print(f"\n  Average Score: {avg_score:.1f}/100")
        
        # Generate recommendations
        print("\n📋 Recommendations:")
        
        if any(score < 90 for score in self.scores.values()):
            print("  ⚠️  Address items with score <90 before merge")
        
        has_critical = any(
            f["severity"] == "CRITICAL"
            for findings in self.findings.values()
            for f in findings
        )
        
        if has_critical:
            print("  🚨 CRITICAL ISSUES FOUND - Must be addressed immediately")
        else:
            print("  ✅ No critical security issues detected")
        
        # Show all findings
        print("\n📌 All Findings:")
        for commit_sha, findings_list in self.findings.items():
            if findings_list:
                print(f"\n  {commit_sha}:")
                for f in findings_list:
                    print(f"    [{f.get('severity', 'INFO')}] {f.get('type', 'General')}: {f.get('message', '')}")
                    if "file" in f:
                        print(f"      File: {f['file']}")
        
        # Final recommendation
        print("\n" + "="*60)
        if avg_score >= 90 and not has_critical:
            print("✅ APPROVED FOR MERGE - All checks passed")
            print("   Next: Deploy to staging for UAT")
        else:
            print("⚠️  CONDITIONAL APPROVAL - Address findings before merge")
        print("="*60)

    def run_full_review(self):
        """Execute full code review"""
        print("\n🔍 Starting Comprehensive Code Review...")
        print(f"   Time: {datetime.now().isoformat()}")
        
        self.analyze_commit_dfa9004()
        self.analyze_commit_d65b1c2()
        self.analyze_commit_9d2c80b()
        
        self.generate_report()


def main():
    analyzer = CodeReviewAnalyzer(repo_path="/home/eevan/ProyectosIA/GRUPO_GAD")
    analyzer.run_full_review()


if __name__ == "__main__":
    main()
