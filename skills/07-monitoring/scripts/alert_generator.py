#!/usr/bin/env python3
"""
Alert Generator — Creates alerting rules from SLO definitions.

Generates alert rules in Prometheus, Datadog, or CloudWatch format based on
Service Level Objectives. Produces alerts for error rate, latency, saturation,
and availability with appropriate severity levels and runbook links.

Usage:
    python alert_generator.py --slo 99.9 --service "my-api" --output alerts/
    python alert_generator.py --slo 99.95 --service "payment-svc" --format datadog --output alerts/
    python alert_generator.py --help
"""

import argparse
import os
import sys
from datetime import datetime, timezone


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate alerting rules from SLO definitions.",
        epilog="Example: python alert_generator.py --slo 99.9 --service my-api --output alerts/",
    )
    parser.add_argument(
        "--slo",
        type=float,
        required=True,
        help="Service Level Objective as a percentage (e.g., 99.9)",
    )
    parser.add_argument(
        "--service",
        type=str,
        required=True,
        help='Service name (e.g., "my-api")',
    )
    parser.add_argument(
        "--output",
        type=str,
        default="alerts/",
        help="Output directory for generated alert rules (default: alerts/)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["prometheus", "datadog", "cloudwatch"],
        default="prometheus",
        help="Alert format to generate (default: prometheus)",
    )
    return parser.parse_args()


def calculate_thresholds(slo_percent):
    """Derive alert thresholds from the SLO target."""
    error_budget = 100.0 - slo_percent  # e.g., 0.1 for 99.9%

    return {
        "slo_target": slo_percent / 100.0,
        "error_budget_percent": error_budget,
        # Critical: burning through error budget 14.4x faster than allowed (consumes budget in ~1h)
        "error_rate_critical": round(error_budget * 14.4 / 100.0, 6),
        # Warning: burning through error budget 6x faster than allowed (consumes budget in ~6h)
        "error_rate_warning": round(error_budget * 6.0 / 100.0, 6),
        # Info: burning through error budget 3x faster than allowed
        "error_rate_info": round(error_budget * 3.0 / 100.0, 6),
        # Latency thresholds (seconds)
        "latency_critical_s": 5.0,
        "latency_warning_s": 2.0,
        "latency_info_s": 1.0,
        # Saturation thresholds (percentage)
        "saturation_critical": 0.95,
        "saturation_warning": 0.85,
        "saturation_info": 0.75,
    }


def generate_prometheus(service, slo_percent, thresholds):
    """Generate Prometheus alerting rules in YAML format."""
    slo_str = str(slo_percent)
    error_budget = thresholds["error_budget_percent"]
    runbook_base = f"https://runbooks.example.com/{service}"
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return f"""# Auto-generated Prometheus alert rules
# Service: {service}
# SLO: {slo_str}% availability ({error_budget}% error budget)
# Generated: {generated_at}
#
# These rules implement multi-window, multi-burn-rate alerting based on
# the SLO target. Adjust thresholds and durations to match your environment.

groups:
  - name: {service}_slo_alerts
    rules:

      # ---------------------------------------------------------------
      # Error Rate Alerts (based on SLO burn rate)
      # ---------------------------------------------------------------

      - alert: {service}_ErrorRateCritical
        expr: |
          (
            sum(rate(http_requests_total{{service="{service}", code=~"5.."}}[5m]))
            /
            sum(rate(http_requests_total{{service="{service}"}}[5m]))
          ) > {thresholds["error_rate_critical"]}
        for: 2m
        labels:
          severity: critical
          service: {service}
          slo: "{slo_str}"
        annotations:
          summary: "Critical error rate for {service}"
          description: >-
            Error rate is above {thresholds["error_rate_critical"] * 100:.2f}% (14.4x burn rate).
            At this rate the monthly error budget will be exhausted in ~1 hour.
            Current value: {{{{ $value | humanizePercentage }}}}.
          runbook_url: "{runbook_base}/error-rate-critical"

      - alert: {service}_ErrorRateWarning
        expr: |
          (
            sum(rate(http_requests_total{{service="{service}", code=~"5.."}}[30m]))
            /
            sum(rate(http_requests_total{{service="{service}"}}[30m]))
          ) > {thresholds["error_rate_warning"]}
        for: 15m
        labels:
          severity: warning
          service: {service}
          slo: "{slo_str}"
        annotations:
          summary: "Elevated error rate for {service}"
          description: >-
            Error rate is above {thresholds["error_rate_warning"] * 100:.2f}% (6x burn rate).
            At this rate the monthly error budget will be exhausted in ~6 hours.
            Current value: {{{{ $value | humanizePercentage }}}}.
          runbook_url: "{runbook_base}/error-rate-warning"

      - alert: {service}_ErrorRateInfo
        expr: |
          (
            sum(rate(http_requests_total{{service="{service}", code=~"5.."}}[6h]))
            /
            sum(rate(http_requests_total{{service="{service}"}}[6h]))
          ) > {thresholds["error_rate_info"]}
        for: 1h
        labels:
          severity: info
          service: {service}
          slo: "{slo_str}"
        annotations:
          summary: "Slightly elevated error rate for {service}"
          description: >-
            Error rate is above {thresholds["error_rate_info"] * 100:.2f}% (3x burn rate).
            Current value: {{{{ $value | humanizePercentage }}}}.
          runbook_url: "{runbook_base}/error-rate-info"

      # ---------------------------------------------------------------
      # Latency Alerts (p99 response time)
      # ---------------------------------------------------------------

      - alert: {service}_LatencyCritical
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_request_duration_seconds_bucket{{service="{service}"}}[5m])) by (le)
          ) > {thresholds["latency_critical_s"]}
        for: 5m
        labels:
          severity: critical
          service: {service}
        annotations:
          summary: "Critical latency for {service}"
          description: >-
            p99 latency is above {thresholds["latency_critical_s"]}s.
            Current value: {{{{ $value | humanizeDuration }}}}.
          runbook_url: "{runbook_base}/latency-critical"

      - alert: {service}_LatencyWarning
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket{{service="{service}"}}[5m])) by (le)
          ) > {thresholds["latency_warning_s"]}
        for: 10m
        labels:
          severity: warning
          service: {service}
        annotations:
          summary: "Elevated latency for {service}"
          description: >-
            p95 latency is above {thresholds["latency_warning_s"]}s.
            Current value: {{{{ $value | humanizeDuration }}}}.
          runbook_url: "{runbook_base}/latency-warning"

      - alert: {service}_LatencyInfo
        expr: |
          histogram_quantile(0.90,
            sum(rate(http_request_duration_seconds_bucket{{service="{service}"}}[5m])) by (le)
          ) > {thresholds["latency_info_s"]}
        for: 15m
        labels:
          severity: info
          service: {service}
        annotations:
          summary: "Latency trending up for {service}"
          description: >-
            p90 latency is above {thresholds["latency_info_s"]}s.
            Current value: {{{{ $value | humanizeDuration }}}}.
          runbook_url: "{runbook_base}/latency-info"

      # ---------------------------------------------------------------
      # Saturation Alerts (resource exhaustion)
      # ---------------------------------------------------------------

      - alert: {service}_SaturationCritical
        expr: |
          (
            sum(container_memory_working_set_bytes{{container="{service}"}})
            /
            sum(container_spec_memory_limit_bytes{{container="{service}"}})
          ) > {thresholds["saturation_critical"]}
        for: 5m
        labels:
          severity: critical
          service: {service}
        annotations:
          summary: "Memory saturation critical for {service}"
          description: >-
            Memory usage is above {thresholds["saturation_critical"] * 100:.0f}% of limit.
            OOM kill is imminent. Current value: {{{{ $value | humanizePercentage }}}}.
          runbook_url: "{runbook_base}/saturation-critical"

      - alert: {service}_SaturationWarning
        expr: |
          (
            sum(container_memory_working_set_bytes{{container="{service}"}})
            /
            sum(container_spec_memory_limit_bytes{{container="{service}"}})
          ) > {thresholds["saturation_warning"]}
        for: 10m
        labels:
          severity: warning
          service: {service}
        annotations:
          summary: "Memory saturation elevated for {service}"
          description: >-
            Memory usage is above {thresholds["saturation_warning"] * 100:.0f}% of limit.
            Current value: {{{{ $value | humanizePercentage }}}}.
          runbook_url: "{runbook_base}/saturation-warning"

      - alert: {service}_CPUSaturationWarning
        expr: |
          (
            sum(rate(container_cpu_usage_seconds_total{{container="{service}"}}[5m]))
            /
            sum(container_spec_cpu_quota{{container="{service}"}}/container_spec_cpu_period{{container="{service}"}})
          ) > {thresholds["saturation_warning"]}
        for: 10m
        labels:
          severity: warning
          service: {service}
        annotations:
          summary: "CPU saturation elevated for {service}"
          description: >-
            CPU usage is above {thresholds["saturation_warning"] * 100:.0f}% of limit.
            Current value: {{{{ $value | humanizePercentage }}}}.
          runbook_url: "{runbook_base}/cpu-saturation-warning"

      # ---------------------------------------------------------------
      # Availability Alert (SLO breach)
      # ---------------------------------------------------------------

      - alert: {service}_AvailabilitySLOBreach
        expr: |
          (
            sum(increase(http_requests_total{{service="{service}", code!~"5.."}}[30d]))
            /
            sum(increase(http_requests_total{{service="{service}"}}[30d]))
          ) < {thresholds["slo_target"]}
        for: 5m
        labels:
          severity: critical
          service: {service}
          slo: "{slo_str}"
        annotations:
          summary: "SLO breach for {service}"
          description: >-
            30-day rolling availability has dropped below the {slo_str}% SLO target.
            Error budget is exhausted. Current availability: {{{{ $value | humanizePercentage }}}}.
          runbook_url: "{runbook_base}/slo-breach"

      - alert: {service}_ErrorBudgetLow
        expr: |
          (
            1 - (
              sum(increase(http_requests_total{{service="{service}", code=~"5.."}}[30d]))
              /
              (sum(increase(http_requests_total{{service="{service}"}}[30d])) * {thresholds["error_budget_percent"] / 100.0})
            )
          ) < 0.25
        for: 1h
        labels:
          severity: warning
          service: {service}
          slo: "{slo_str}"
        annotations:
          summary: "Error budget running low for {service}"
          description: >-
            Less than 25% of the monthly error budget remains for {service}.
            Consider freezing risky deployments. Remaining: {{{{ $value | humanizePercentage }}}}.
          runbook_url: "{runbook_base}/error-budget-low"
"""


def generate_datadog(service, slo_percent, thresholds):
    """Generate Datadog monitor definitions in YAML format."""
    error_budget = thresholds["error_budget_percent"]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return f"""# Auto-generated Datadog monitor definitions
# Service: {service}
# SLO: {slo_percent}% availability ({error_budget}% error budget)
# Generated: {generated_at}
#
# Import these monitors using the Datadog API or Terraform provider.

monitors:

  - name: "[{service}] Error Rate Critical"
    type: query alert
    query: >-
      sum(last_5m):sum:http.requests.errors{{service:{service}}}.as_rate()
      / sum:http.requests.total{{service:{service}}}.as_rate() > {thresholds["error_rate_critical"]}
    message: |
      {{{{#is_alert}}}}
      CRITICAL: Error rate for {service} is above {thresholds["error_rate_critical"] * 100:.2f}%.
      At this burn rate the monthly error budget will be exhausted in ~1 hour.

      Runbook: https://runbooks.example.com/{service}/error-rate-critical
      {{{{/is_alert}}}}

      {{{{#is_recovery}}}}
      RECOVERED: Error rate for {service} has returned to normal.
      {{{{/is_recovery}}}}
    tags:
      - service:{service}
      - slo:{slo_percent}
      - severity:critical
    options:
      thresholds:
        critical: {thresholds["error_rate_critical"]}
        warning: {thresholds["error_rate_warning"]}
      notify_no_data: true
      no_data_timeframe: 10
      renotify_interval: 15

  - name: "[{service}] Error Rate Warning"
    type: query alert
    query: >-
      sum(last_30m):sum:http.requests.errors{{service:{service}}}.as_rate()
      / sum:http.requests.total{{service:{service}}}.as_rate() > {thresholds["error_rate_warning"]}
    message: |
      {{{{#is_alert}}}}
      WARNING: Error rate for {service} is above {thresholds["error_rate_warning"] * 100:.2f}%.

      Runbook: https://runbooks.example.com/{service}/error-rate-warning
      {{{{/is_alert}}}}
    tags:
      - service:{service}
      - slo:{slo_percent}
      - severity:warning
    options:
      thresholds:
        critical: {thresholds["error_rate_warning"]}
      renotify_interval: 60

  - name: "[{service}] Latency p99 Critical"
    type: query alert
    query: >-
      avg(last_5m):p99:http.request.duration{{service:{service}}} > {thresholds["latency_critical_s"]}
    message: |
      {{{{#is_alert}}}}
      CRITICAL: p99 latency for {service} is above {thresholds["latency_critical_s"]}s.

      Runbook: https://runbooks.example.com/{service}/latency-critical
      {{{{/is_alert}}}}
    tags:
      - service:{service}
      - severity:critical
    options:
      thresholds:
        critical: {thresholds["latency_critical_s"]}
        warning: {thresholds["latency_warning_s"]}

  - name: "[{service}] Latency p95 Warning"
    type: query alert
    query: >-
      avg(last_10m):p95:http.request.duration{{service:{service}}} > {thresholds["latency_warning_s"]}
    message: |
      {{{{#is_alert}}}}
      WARNING: p95 latency for {service} is above {thresholds["latency_warning_s"]}s.

      Runbook: https://runbooks.example.com/{service}/latency-warning
      {{{{/is_alert}}}}
    tags:
      - service:{service}
      - severity:warning
    options:
      thresholds:
        critical: {thresholds["latency_warning_s"]}

  - name: "[{service}] Memory Saturation Critical"
    type: query alert
    query: >-
      avg(last_5m):avg:container.memory.usage{{service:{service}}}
      / avg:container.memory.limit{{service:{service}}} > {thresholds["saturation_critical"]}
    message: |
      {{{{#is_alert}}}}
      CRITICAL: Memory usage for {service} is above {thresholds["saturation_critical"] * 100:.0f}%.
      OOM kill is imminent.

      Runbook: https://runbooks.example.com/{service}/saturation-critical
      {{{{/is_alert}}}}
    tags:
      - service:{service}
      - severity:critical
    options:
      thresholds:
        critical: {thresholds["saturation_critical"]}
        warning: {thresholds["saturation_warning"]}

  - name: "[{service}] SLO Breach"
    type: slo alert
    slo:
      type: metric
      target: {slo_percent}
      timeframe: 30d
      query:
        numerator: sum:http.requests.total{{service:{service},NOT code:5*}}.as_count()
        denominator: sum:http.requests.total{{service:{service}}}.as_count()
    message: |
      {{{{#is_alert}}}}
      CRITICAL: {service} has breached its {slo_percent}% availability SLO.
      Error budget is exhausted. Freeze non-critical deployments.

      Runbook: https://runbooks.example.com/{service}/slo-breach
      {{{{/is_alert}}}}
    tags:
      - service:{service}
      - slo:{slo_percent}
      - severity:critical
"""


def generate_cloudwatch(service, slo_percent, thresholds):
    """Generate AWS CloudWatch alarm definitions in YAML (CloudFormation-style) format."""
    error_budget = thresholds["error_budget_percent"]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # CloudWatch-safe name (alphanumeric and hyphens only)
    safe_name = service.replace("_", "-").replace(".", "-")

    return f"""# Auto-generated CloudWatch alarm definitions (CloudFormation-style)
# Service: {service}
# SLO: {slo_percent}% availability ({error_budget}% error budget)
# Generated: {generated_at}
#
# Add these resources to your CloudFormation template or convert to Terraform.

AWSTemplateFormatVersion: "2010-09-09"
Description: "Monitoring alarms for {service} (SLO: {slo_percent}%)"

Parameters:
  SNSTopicArn:
    Type: String
    Description: SNS topic ARN for alarm notifications

Resources:

  # ---------------------------------------------------------------
  # Error Rate Alarms
  # ---------------------------------------------------------------

  {safe_name}ErrorRateCritical:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: "{service}-error-rate-critical"
      AlarmDescription: >-
        Critical: Error rate for {service} exceeds {thresholds["error_rate_critical"] * 100:.2f}%
        (14.4x SLO burn rate). Runbook: https://runbooks.example.com/{service}/error-rate-critical
      Namespace: "Custom/{service}"
      MetricName: "ErrorRate"
      Statistic: Average
      Period: 300
      EvaluationPeriods: 1
      Threshold: {thresholds["error_rate_critical"]}
      ComparisonOperator: GreaterThanThreshold
      TreatMissingData: breaching
      AlarmActions:
        - !Ref SNSTopicArn
      OKActions:
        - !Ref SNSTopicArn
      Tags:
        - Key: Service
          Value: {service}
        - Key: Severity
          Value: critical
        - Key: SLO
          Value: "{slo_percent}"

  {safe_name}ErrorRateWarning:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: "{service}-error-rate-warning"
      AlarmDescription: >-
        Warning: Error rate for {service} exceeds {thresholds["error_rate_warning"] * 100:.2f}%
        (6x SLO burn rate). Runbook: https://runbooks.example.com/{service}/error-rate-warning
      Namespace: "Custom/{service}"
      MetricName: "ErrorRate"
      Statistic: Average
      Period: 1800
      EvaluationPeriods: 1
      Threshold: {thresholds["error_rate_warning"]}
      ComparisonOperator: GreaterThanThreshold
      TreatMissingData: notBreaching
      AlarmActions:
        - !Ref SNSTopicArn
      Tags:
        - Key: Service
          Value: {service}
        - Key: Severity
          Value: warning

  # ---------------------------------------------------------------
  # Latency Alarms
  # ---------------------------------------------------------------

  {safe_name}LatencyCritical:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: "{service}-latency-p99-critical"
      AlarmDescription: >-
        Critical: p99 latency for {service} exceeds {thresholds["latency_critical_s"]}s.
        Runbook: https://runbooks.example.com/{service}/latency-critical
      Namespace: "Custom/{service}"
      MetricName: "ResponseTime"
      ExtendedStatistic: "p99"
      Period: 300
      EvaluationPeriods: 1
      Threshold: {thresholds["latency_critical_s"]}
      ComparisonOperator: GreaterThanThreshold
      TreatMissingData: notBreaching
      AlarmActions:
        - !Ref SNSTopicArn
      Tags:
        - Key: Service
          Value: {service}
        - Key: Severity
          Value: critical

  {safe_name}LatencyWarning:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: "{service}-latency-p95-warning"
      AlarmDescription: >-
        Warning: p95 latency for {service} exceeds {thresholds["latency_warning_s"]}s.
        Runbook: https://runbooks.example.com/{service}/latency-warning
      Namespace: "Custom/{service}"
      MetricName: "ResponseTime"
      ExtendedStatistic: "p95"
      Period: 300
      EvaluationPeriods: 2
      Threshold: {thresholds["latency_warning_s"]}
      ComparisonOperator: GreaterThanThreshold
      TreatMissingData: notBreaching
      AlarmActions:
        - !Ref SNSTopicArn
      Tags:
        - Key: Service
          Value: {service}
        - Key: Severity
          Value: warning

  # ---------------------------------------------------------------
  # Saturation Alarms
  # ---------------------------------------------------------------

  {safe_name}MemorySaturationCritical:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: "{service}-memory-saturation-critical"
      AlarmDescription: >-
        Critical: Memory usage for {service} exceeds {thresholds["saturation_critical"] * 100:.0f}%.
        OOM kill imminent. Runbook: https://runbooks.example.com/{service}/saturation-critical
      Namespace: "AWS/ECS"
      MetricName: "MemoryUtilization"
      Dimensions:
        - Name: ServiceName
          Value: {service}
      Statistic: Average
      Period: 300
      EvaluationPeriods: 1
      Threshold: {thresholds["saturation_critical"] * 100}
      ComparisonOperator: GreaterThanThreshold
      AlarmActions:
        - !Ref SNSTopicArn
      Tags:
        - Key: Service
          Value: {service}
        - Key: Severity
          Value: critical

  {safe_name}CPUSaturationWarning:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: "{service}-cpu-saturation-warning"
      AlarmDescription: >-
        Warning: CPU usage for {service} exceeds {thresholds["saturation_warning"] * 100:.0f}%.
        Runbook: https://runbooks.example.com/{service}/cpu-saturation-warning
      Namespace: "AWS/ECS"
      MetricName: "CPUUtilization"
      Dimensions:
        - Name: ServiceName
          Value: {service}
      Statistic: Average
      Period: 300
      EvaluationPeriods: 2
      Threshold: {thresholds["saturation_warning"] * 100}
      ComparisonOperator: GreaterThanThreshold
      AlarmActions:
        - !Ref SNSTopicArn
      Tags:
        - Key: Service
          Value: {service}
        - Key: Severity
          Value: warning

  # ---------------------------------------------------------------
  # Availability / SLO Composite Alarm
  # ---------------------------------------------------------------

  {safe_name}SLOBreachComposite:
    Type: AWS::CloudWatch::CompositeAlarm
    Properties:
      AlarmName: "{service}-slo-breach"
      AlarmDescription: >-
        SLO breach: Multiple critical alarms are firing for {service}.
        Error budget is likely exhausted. Freeze non-critical deployments.
        Runbook: https://runbooks.example.com/{service}/slo-breach
      AlarmRule: >-
        ALARM("{service}-error-rate-critical")
        AND
        (ALARM("{service}-latency-p99-critical")
         OR ALARM("{service}-memory-saturation-critical"))
      AlarmActions:
        - !Ref SNSTopicArn
      Tags:
        - Key: Service
          Value: {service}
        - Key: Severity
          Value: critical
        - Key: SLO
          Value: "{slo_percent}"
"""


def main():
    args = parse_args()

    if args.slo <= 0 or args.slo >= 100:
        print("Error: SLO must be between 0 and 100 (exclusive).", file=sys.stderr)
        sys.exit(1)

    thresholds = calculate_thresholds(args.slo)

    generators = {
        "prometheus": generate_prometheus,
        "datadog": generate_datadog,
        "cloudwatch": generate_cloudwatch,
    }

    extensions = {
        "prometheus": "yml",
        "datadog": "yml",
        "cloudwatch": "yml",
    }

    generator = generators[args.format]
    content = generator(args.service, args.slo, thresholds)

    os.makedirs(args.output, exist_ok=True)

    filename = f"{args.service}-alerts-{args.format}.{extensions[args.format]}"
    filepath = os.path.join(args.output, filename)

    with open(filepath, "w") as f:
        f.write(content)

    print(f"Generated {args.format} alert rules for '{args.service}' (SLO: {args.slo}%)")
    print(f"  Error budget: {thresholds['error_budget_percent']}%")
    print(f"  Critical error rate threshold: {thresholds['error_rate_critical'] * 100:.4f}%")
    print(f"  Warning error rate threshold:  {thresholds['error_rate_warning'] * 100:.4f}%")
    print(f"  Output: {filepath}")


if __name__ == "__main__":
    main()
