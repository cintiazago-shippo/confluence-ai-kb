#!/usr/bin/env python
"""
Generate fake Confluence data for testing the AI Knowledge Base
"""

import sys
import os
import uuid
from datetime import datetime, timedelta
import random
import json

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from database.init_db import get_session, init_database
from database.models import ConfluencePage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample data templates
BUSINESS_RULES = [
    {
        "title": "Purchase Order Approval Process",
        "content": """
        # Purchase Order Approval Process

        ## Overview
        This document outlines the approval process for purchase orders within our organization.

        ## Approval Thresholds
        - Orders under $1,000: Direct manager approval
        - Orders $1,000 - $10,000: Department head approval required
        - Orders $10,000 - $50,000: VP approval required
        - Orders over $50,000: CFO approval required

        ## Process Steps
        1. Employee creates purchase request in the system
        2. System automatically routes to appropriate approver based on amount
        3. Approver receives email notification
        4. Approver reviews and approves/rejects within 48 hours
        5. Upon approval, purchase order is sent to vendor
        6. Finance team is notified for budget tracking

        ## Emergency Orders
        For urgent purchases, use the expedited approval process:
        - Mark as "Emergency" in the system
        - Provide justification
        - Approval timeline reduced to 4 hours during business days

        ## Compliance Requirements
        All purchase orders must include:
        - Vendor tax information
        - Budget code
        - Project allocation (if applicable)
        - Business justification
        """
    },
    {
        "title": "Employee Onboarding Process",
        "content": """
        # Employee Onboarding Process

        ## Pre-Arrival (Day -7 to Day -1)
        ### HR Tasks
        - Send welcome email with first-day information
        - Prepare workspace and equipment
        - Create user accounts (email, Slack, etc.)
        - Schedule orientation meetings
        - Prepare onboarding packet

        ### IT Tasks
        - Order and configure laptop/desktop
        - Set up email and calendar
        - Create Active Directory account
        - Assign software licenses
        - Configure VPN access

        ## First Day (Day 1)
        ### Morning (9:00 AM - 12:00 PM)
        - Welcome and office tour
        - IT setup and equipment distribution
        - Security badge photo and activation
        - Complete I-9 verification
        - Review employee handbook

        ### Afternoon (1:00 PM - 5:00 PM)
        - Meet with direct manager
        - Team introductions
        - Review role expectations
        - Set up workspace
        - Complete mandatory training modules

        ## First Week Activities
        - Department overview presentations
        - Product/service training
        - Shadow team members
        - Complete benefits enrollment
        - Safety training completion

        ## 30-Day Checkpoint
        - Manager check-in meeting
        - Address any questions or concerns
        - Confirm benefits selections
        - Review initial performance goals
        - Gather feedback on onboarding experience

        ## Required Documentation
        - Signed offer letter
        - I-9 documentation
        - Tax forms (W-4)
        - Direct deposit information
        - Emergency contact information
        - Signed confidentiality agreement
        """
    },
    {
        "title": "Data Retention and Privacy Policy",
        "content": """
        # Data Retention and Privacy Policy

        ## Purpose
        This policy establishes guidelines for data retention and privacy protection across all company systems.

        ## Data Classification
        ### Confidential Data
        - Customer personal information (PII)
        - Financial records
        - Employee records
        - Proprietary business information
        - Retention: 7 years

        ### Internal Data
        - Internal communications
        - Project documentation
        - Meeting notes
        - Retention: 3 years

        ### Public Data
        - Marketing materials
        - Published content
        - Press releases
        - Retention: Indefinite

        ## Customer Data Protection
        ### Collection Principles
        - Collect only necessary information
        - Obtain explicit consent
        - Provide clear privacy notices
        - Allow opt-out options

        ### Storage Requirements
        - Encrypt all PII at rest and in transit
        - Store in approved systems only
        - Limit access to authorized personnel
        - Maintain access logs

        ### Data Subject Rights
        - Right to access their data
        - Right to correction
        - Right to deletion (where applicable)
        - Right to data portability

        ## Retention Schedules
        - Customer transaction data: 7 years
        - Email communications: 3 years
        - System logs: 1 year
        - Backup data: 90 days
        - Marketing analytics: 2 years

        ## Data Disposal
        - Electronic data: Secure deletion using approved tools
        - Physical documents: Shredding required
        - Certificates of destruction required
        - Quarterly disposal reviews

        ## Compliance
        - GDPR compliance for EU customers
        - CCPA compliance for California residents
        - Regular privacy audits
        - Annual training required
        """
    },
    {
        "title": "Code Review Guidelines",
        "content": """
        # Code Review Guidelines

        ## Purpose
        Establish consistent code review practices to maintain code quality and share knowledge.

        ## Review Process
        ### Before Submitting for Review
        - Run all tests locally
        - Ensure code follows style guide
        - Self-review your changes
        - Update documentation if needed
        - Write clear commit messages

        ### Creating Pull Requests
        - Use descriptive PR titles
        - Include ticket/issue number
        - Describe what changed and why
        - List any breaking changes
        - Include testing instructions

        ### Review Checklist
        #### Code Quality
        - [ ] Follows coding standards
        - [ ] No code duplication
        - [ ] Clear variable and function names
        - [ ] Appropriate comments
        - [ ] Error handling implemented

        #### Architecture
        - [ ] Follows established patterns
        - [ ] Maintains separation of concerns
        - [ ] Scalable approach
        - [ ] Performance considered
        - [ ] Security best practices

        #### Testing
        - [ ] Unit tests included
        - [ ] Integration tests if applicable
        - [ ] Edge cases covered
        - [ ] Tests are maintainable
        - [ ] Coverage meets standards (80%+)

        ## Review Etiquette
        ### For Reviewers
        - Respond within 24 hours
        - Be constructive and specific
        - Suggest improvements, don't just criticize
        - Approve if no major issues
        - Use "Request Changes" sparingly

        ### For Authors
        - Respond to all comments
        - Be open to feedback
        - Explain decisions when needed
        - Update PR based on feedback
        - Don't take feedback personally

        ## Approval Requirements
        - Minimum 2 approvals for production code
        - 1 approval for documentation changes
        - Team lead approval for architectural changes
        - Security team approval for auth changes
        """
    },
    {
        "title": "Incident Response Procedures",
        "content": """
        # Incident Response Procedures

        ## Incident Classification
        ### Severity 1 (Critical)
        - Complete service outage
        - Data breach or security incident
        - Revenue impact > $10K/hour
        - Response time: 15 minutes

        ### Severity 2 (High)
        - Partial service degradation
        - Major feature unavailable
        - Revenue impact < $10K/hour
        - Response time: 30 minutes

        ### Severity 3 (Medium)
        - Minor feature issues
        - Performance degradation
        - No direct revenue impact
        - Response time: 2 hours

        ### Severity 4 (Low)
        - Cosmetic issues
        - Non-critical bugs
        - Response time: Next business day

        ## Response Process
        ### 1. Detection and Alert
        - Monitoring system alerts
        - Customer reports
        - Internal discovery
        - Log incident in tracking system

        ### 2. Initial Response
        - Acknowledge incident
        - Assess severity
        - Notify on-call engineer
        - Create incident channel (#inc-YYYY-MM-DD-XXX)

        ### 3. Escalation
        #### Severity 1-2 Escalation
        - Page on-call engineer
        - Notify team lead
        - Alert management chain
        - Prepare status page update

        #### Communication
        - Update status page within 30 minutes
        - Send customer notifications if needed
        - Internal updates every 30 minutes
        - Executive updates for Sev 1

        ### 4. Resolution
        - Implement fix or workaround
        - Verify resolution
        - Monitor for stability
        - Update all stakeholders

        ### 5. Post-Incident
        - Post-mortem within 48 hours (Sev 1-2)
        - Document root cause
        - Create action items
        - Share learnings with team

        ## On-Call Responsibilities
        - Primary: Respond within SLA
        - Secondary: Available as backup
        - Escalation: Management chain
        - Handoff: Detailed documentation required

        ## Contact Information
        - On-call phone: +1-800-XXX-XXXX
        - Escalation: See on-call schedule
        - Security team: security@company.com
        - Legal team: legal@company.com
        """
    }
]

PROJECT_DOCS = [
    {
        "title": "Project Phoenix - Mobile App Redesign",
        "content": """
        # Project Phoenix - Mobile App Redesign

        ## Project Overview
        Complete redesign of our mobile application to improve user experience and modernize the technology stack.

        ## Timeline
        - Project Start: January 15, 2024
        - Design Phase: January 15 - March 1, 2024
        - Development: March 1 - August 15, 2024
        - Testing: August 15 - September 30, 2024
        - Launch: October 15, 2024

        ## Stakeholders
        - Project Sponsor: Sarah Johnson (VP Product)
        - Project Manager: Michael Chen
        - Tech Lead: Emily Rodriguez
        - Design Lead: James Wilson
        - QA Lead: Maria Garcia

        ## Success Criteria
        1. Increase user engagement by 25%
        2. Reduce app crash rate to < 0.5%
        3. Improve app store rating to 4.5+ stars
        4. Reduce customer support tickets by 30%
        5. Page load time < 2 seconds

        ## Technical Requirements
        ### Platform Support
        - iOS 14.0+
        - Android 8.0+
        - Tablet optimization

        ### Key Features
        - Biometric authentication
        - Offline mode support
        - Push notifications
        - Real-time sync
        - Dark mode

        ### Technology Stack
        - Frontend: React Native
        - Backend: Node.js + GraphQL
        - Database: PostgreSQL
        - Cache: Redis
        - Analytics: Mixpanel

        ## Budget
        - Total Budget: $850,000
        - Development: $500,000
        - Design: $150,000
        - Testing: $100,000
        - Marketing: $100,000

        ## Risk Management
        - iOS approval delays: Submit early
        - Third-party API changes: Version locking
        - Performance issues: Regular profiling
        - Scope creep: Strict change control
        """
    },
    {
        "title": "API Gateway Migration Strategy",
        "content": """
        # API Gateway Migration Strategy

        ## Executive Summary
        Migrate from legacy API infrastructure to modern API Gateway solution to improve scalability, security, and developer experience.

        ## Current State
        ### Problems
        - Multiple API endpoints across services
        - Inconsistent authentication methods
        - No centralized rate limiting
        - Limited monitoring and analytics
        - Manual API documentation

        ### Current Architecture
        - 15 microservices with individual APIs
        - Mixed authentication (OAuth, API keys, JWT)
        - No unified logging
        - Point-to-point communication

        ## Target State
        ### API Gateway Features
        - Single entry point for all APIs
        - Unified authentication/authorization
        - Rate limiting and throttling
        - Request/response transformation
        - Centralized logging and monitoring

        ### Technology Selection
        After evaluation, selected Kong Gateway for:
        - Open-source with enterprise option
        - Plugin ecosystem
        - Kubernetes native
        - High performance (50k+ req/sec)

        ## Migration Plan
        ### Phase 1: Setup (Q1 2024)
        - Deploy Kong in development
        - Configure basic plugins
        - Create CI/CD pipeline
        - Train team on Kong

        ### Phase 2: Service Migration (Q2-Q3 2024)
        - Migrate authentication service
        - Migrate user service
        - Migrate payment service
        - Migrate notification service
        - Run in parallel with legacy

        ### Phase 3: Advanced Features (Q4 2024)
        - Implement rate limiting
        - Add request transformation
        - Enable API versioning
        - Set up developer portal

        ### Phase 4: Deprecation (Q1 2025)
        - Monitor legacy API usage
        - Communicate deprecation timeline
        - Assist remaining consumers
        - Decommission legacy APIs

        ## Success Metrics
        - API response time < 100ms
        - 99.95% uptime SLA
        - Zero security incidents
        - 50% reduction in API support tickets
        - Developer satisfaction score > 4.5/5
        """
    },
    {
        "title": "Q4 2024 OKRs and Initiatives",
        "content": """
        # Q4 2024 OKRs and Initiatives

        ## Company Level OKRs

        ### Objective 1: Accelerate Revenue Growth
        - KR1: Achieve $15M in Q4 revenue (20% QoQ growth)
        - KR2: Increase enterprise accounts by 25%
        - KR3: Reduce customer churn to < 5%
        - KR4: Launch 2 new revenue streams

        ### Objective 2: Enhance Product Excellence
        - KR1: Ship 5 major features from roadmap
        - KR2: Achieve 95%+ uptime across all services
        - KR3: Reduce average bug resolution time to < 48 hours
        - KR4: Increase NPS score to 50+

        ### Objective 3: Build World-Class Team
        - KR1: Hire 25 key positions
        - KR2: Achieve 85%+ employee satisfaction
        - KR3: Complete leadership training for all managers
        - KR4: Reduce voluntary turnover to < 10%

        ## Department Initiatives

        ### Engineering
        - Complete microservices migration
        - Implement automated testing framework
        - Reduce deployment time by 50%
        - Launch internal developer platform

        ### Product
        - User research for 2025 roadmap
        - A/B testing framework rollout
        - Competitive analysis deep dive
        - Customer advisory board setup

        ### Sales
        - Enterprise sales playbook
        - Partner channel program
        - Sales automation tools
        - Account-based marketing pilot

        ### Marketing
        - Rebrand launch
        - Content marketing scaling
        - Event strategy for 2025
        - Marketing automation setup

        ## Key Dates
        - October 15: Mid-quarter review
        - November 1: 2025 planning kickoff
        - November 30: Hiring freeze (if needed)
        - December 15: Q4 wrap-up begins

        ## Budget Allocation
        - Engineering: $3.5M
        - Sales & Marketing: $2.8M
        - Product: $1.2M
        - Operations: $1.5M
        - Reserve: $1M

        ## Risk Mitigation
        - Economic downturn: Focus on enterprise
        - Competitor moves: Accelerate roadmap
        - Talent shortage: Increase referral bonus
        - Technical debt: Dedicated sprint time
        """
    }
]

TECHNICAL_DOCS = [
    {
        "title": "Payment Gateway Integration Guide",
        "content": """
        # Payment Gateway Integration Guide

        ## Overview
        This guide covers integration with our payment processing system using Stripe as the primary gateway.

        ## API Authentication
        ### API Keys
        ```
        Test Mode: sk_test_51234567890abcdefghijk
        Live Mode: sk_live_[obtain from DevOps]
        ```

        ### Headers Required
        ```
        Authorization: Bearer {API_KEY}
        Content-Type: application/json
        X-Idempotency-Key: {unique-request-id}
        ```

        ## Integration Steps

        ### 1. Initialize Payment Intent
        ```python
        POST /api/v1/payments/intent
        {
            "amount": 5000,  # Amount in cents
            "currency": "usd",
            "customer_id": "cust_123456",
            "metadata": {
                "order_id": "ord_789",
                "product_id": "prod_456"
            }
        }
        ```

        ### 2. Confirm Payment
        ```python
        POST /api/v1/payments/confirm
        {
            "payment_intent_id": "pi_1234567890",
            "payment_method": "pm_card_visa"
        }
        ```

        ### 3. Handle Webhooks
        Configure webhook endpoint: `https://api.company.com/webhooks/stripe`

        Events to handle:
        - payment_intent.succeeded
        - payment_intent.failed
        - payment_intent.canceled
        - charge.dispute.created

        ## Error Handling
        ### Common Error Codes
        - 400: Invalid request parameters
        - 401: Authentication failed
        - 402: Payment required
        - 409: Duplicate payment
        - 429: Rate limit exceeded

        ### Retry Logic
        - Use exponential backoff
        - Maximum 3 retries
        - Retry only on 5xx errors

        ## Security Requirements
        - Always use HTTPS
        - Validate webhook signatures
        - Store sensitive data encrypted
        - PCI compliance required
        - Regular security audits

        ## Rate Limits
        - 100 requests per minute per API key
        - 10,000 requests per day
        - Webhook events: unlimited
        - Burst allowance: 200 requests

        ## Testing
        ### Test Card Numbers
        - Success: 4242 4242 4242 4242
        - Decline: 4000 0000 0000 0002
        - 3D Secure: 4000 0000 0000 3220
        """
    },
    {
        "title": "Production Deployment Process",
        "content": """
        # Production Deployment Process

        ## Pre-Deployment Checklist
        - [ ] Code review approved by 2+ engineers
        - [ ] All tests passing (unit, integration, e2e)
        - [ ] Security scan completed
        - [ ] Performance testing done
        - [ ] Documentation updated
        - [ ] Database migrations tested
        - [ ] Rollback plan prepared
        - [ ] Stakeholders notified

        ## Deployment Windows
        ### Standard Deployments
        - Tuesday - Thursday
        - 2:00 PM - 4:00 PM PST
        - Avoid month-end and holidays

        ### Emergency Deployments
        - Requires VP approval
        - Incident must be Sev 1 or 2
        - Follow emergency protocol

        ## Deployment Steps

        ### 1. Pre-Deployment (T-30 minutes)
        ```bash
        # Create deployment branch
        git checkout -b deploy/v1.2.3
        git merge main

        # Run final checks
        ./scripts/pre-deploy-check.sh

        # Notify #deployments channel
        @here Deploying v1.2.3 in 30 minutes
        ```

        ### 2. Database Migration (T-15 minutes)
        ```bash
        # Backup production database
        ./scripts/backup-prod-db.sh

        # Run migrations
        kubectl exec -it postgres-primary -- psql -U postgres -d production -f migrations/v1.2.3.sql

        # Verify migration
        ./scripts/verify-migration.sh v1.2.3
        ```

        ### 3. Deploy to Canary (T-0)
        ```bash
        # Deploy to 5% of traffic
        kubectl apply -f k8s/canary/deployment.yaml

        # Monitor for 15 minutes
        watch -n 5 kubectl get pods -n production
        ```

        ### 4. Full Deployment (T+15)
        ```bash
        # If canary healthy, deploy to all
        kubectl apply -f k8s/production/deployment.yaml

        # Watch rollout
        kubectl rollout status deployment/api -n production
        ```

        ### 5. Post-Deployment (T+30)
        ```bash
        # Run smoke tests
        ./scripts/smoke-tests.sh production

        # Check monitoring dashboards
        # - Error rates
        # - Response times
        # - CPU/Memory usage

        # Update status page
        ```

        ## Rollback Procedure
        ```bash
        # Immediate rollback
        kubectl rollout undo deployment/api -n production

        # Restore database if needed
        ./scripts/restore-db.sh $BACKUP_ID

        # Notify stakeholders
        ```

        ## Monitoring Links
        - Grafana: https://grafana.company.com
        - Datadog: https://app.datadoghq.com
        - Sentry: https://sentry.company.com
        - Status Page: https://status.company.com
        """
    }
]


def generate_fake_pages(session, num_pages=20):
    """Generate fake Confluence pages with realistic content"""

    # Combine all templates
    all_templates = BUSINESS_RULES + PROJECT_DOCS + TECHNICAL_DOCS

    # Space keys to use
    space_keys = ["IT", "HR", "PROJ", "DEV", "OPS", "PROD"]

    pages_created = 0

    # First, insert all template pages
    for template in all_templates:
        page = ConfluencePage(
            page_id=str(random.randint(100000, 999999)),
            title=template["title"],
            space_key=random.choice(space_keys),
            content=template["content"].strip(),
            url=f"https://confluence.example.com/display/{random.choice(space_keys)}/{template['title'].replace(' ', '+')}",
            created_at=datetime.now() - timedelta(days=random.randint(30, 365)),
            updated_at=datetime.now() - timedelta(days=random.randint(1, 30)),
            last_modified=datetime.now() - timedelta(days=random.randint(1, 30))
        )
        session.add(page)
        pages_created += 1
        logger.info(f"Created page: {page.title}")

    # Generate additional random pages if needed
    additional_titles = [
        "Security Best Practices",
        "Database Backup Procedures",
        "Customer Support Escalation Process",
        "Release Notes Template",
        "Architecture Decision Records",
        "Performance Optimization Guide",
        "Disaster Recovery Plan",
        "API Documentation Standards",
        "Team Onboarding Checklist",
        "Budget Planning Process",
        "Vendor Management Guidelines",
        "Change Management Process",
        "Quality Assurance Standards",
        "DevOps Best Practices",
        "Cloud Migration Strategy"
    ]

    while pages_created < num_pages and additional_titles:
        title = additional_titles.pop(0)

        # Generate content based on title
        content = f"""
        # {title}

        ## Overview
        This document provides guidelines and procedures for {title.lower()}.

        ## Key Principles
        1. Follow established standards and best practices
        2. Ensure compliance with company policies
        3. Maintain detailed documentation
        4. Regular reviews and updates required

        ## Process Steps
        1. Initial assessment and planning
        2. Stakeholder approval and sign-off
        3. Implementation following guidelines
        4. Testing and validation
        5. Documentation and knowledge transfer

        ## Responsibilities
        - Process Owner: Department Head
        - Implementation: Team Members
        - Review: Quality Assurance
        - Approval: Management

        ## Related Documents
        - Company Policy Manual
        - Technical Standards Guide
        - Compliance Requirements

        Last updated: {datetime.now().strftime('%Y-%m-%d')}
        """

        page = ConfluencePage(
            page_id=str(random.randint(100000, 999999)),
            title=title,
            space_key=random.choice(space_keys),
            content=content.strip(),
            url=f"https://confluence.example.com/display/{random.choice(space_keys)}/{title.replace(' ', '+')}",
            created_at=datetime.now() - timedelta(days=random.randint(30, 365)),
            updated_at=datetime.now() - timedelta(days=random.randint(1, 30)),
            last_modified=datetime.now() - timedelta(days=random.randint(1, 30))
        )
        session.add(page)
        pages_created += 1
        logger.info(f"Created page: {page.title}")

    return pages_created


def main():
    """Main function to generate fake data"""
    print("Generating Fake Confluence Data")
    print("=" * 50)

    # Initialize database
    init_database()

    # Get session
    session = get_session()

    try:
        # Check if data already exists
        existing_count = session.query(ConfluencePage).count()
        if existing_count > 0:
            response = input(f"\nFound {existing_count} existing pages. Delete and regenerate? (y/n): ")
            if response.lower() == 'y':
                session.query(ConfluencePage).delete()
                session.commit()
                logger.info("Deleted existing pages")
            else:
                logger.info("Keeping existing pages")

        # Generate fake pages
        num_pages = 20  # Default number of pages
        pages_created = generate_fake_pages(session, num_pages)

        # Commit changes
        session.commit()

        print(f"\n✅ Successfully created {pages_created} fake Confluence pages!")
        print("\nSample pages created:")

        # Show sample of created pages
        sample_pages = session.query(ConfluencePage).limit(5).all()
        for page in sample_pages:
            print(f"  - {page.title} (Space: {page.space_key})")

        print(f"\nTotal pages in database: {session.query(ConfluencePage).count()}")
        print("\nNext steps:")
        print("1. Run: python scripts/train_model.py")
        print("2. Run: python main.py")

    except Exception as e:
        logger.error(f"Error generating fake data: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()