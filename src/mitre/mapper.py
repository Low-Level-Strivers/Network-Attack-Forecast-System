"""
MITRE ATT&CK Semantic Mapping Module.
Translates predicted attack stages and physical network behavioural signatures
into actionable MITRE ATT&CK tactics, techniques, and SOC defensive advisories.
"""

from typing import Dict, Any, List

MITRE_TACTIC_DATABASE = {
    0: {
        "stage_name": "Normal Baseline",
        "tactic_id": "None",
        "tactic_name": "Normal Operations",
        "technique_id": "N/A",
        "technique_name": "Normal Traffic",
        "description": "Network state features and traffic parameters operate within standard statistical baseline bounds.",
        "severity": "CLEAN",
        "mitigations": [
            "Maintain continuous baseline telemetry and threshold monitoring.",
            "Verify network segment baseline bounds periodically."
        ]
    },
    1: {
        "stage_name": "Reconnaissance",
        "tactic_id": "TA0043 / TA0007",
        "tactic_name": "Reconnaissance / Discovery",
        "technique_id": "T1046",
        "technique_name": "Network Service Discovery / Port Scanning",
        "description": "Adversary is actively probing IP addresses and destination ports to map vulnerable services across the subnet.",
        "severity": "LOW / MEDIUM",
        "mitigations": [
            "Activate dynamic firewall port-scan throttling (drop unreplied SYN bursts).",
            "Obfuscate internal service banners on perimeter gateways.",
            "Alert SOC of prospective horizontal scan reconnaissance targeting internal segments."
        ]
    },
    2: {
        "stage_name": "Credential Access",
        "tactic_id": "TA0006",
        "tactic_name": "Credential Access",
        "technique_id": "T1110.001",
        "technique_name": "Brute Force: Password Guessing (FTP / SSH)",
        "description": "Rapid, repeated authentication transactions detected against remote administration ports (e.g. Port 21/FTP, Port 22/SSH).",
        "severity": "HIGH",
        "mitigations": [
            "Enforce strict account lockout thresholds and progressive authentication delays.",
            "Deploy Fail2ban / automated ACL blacklisting for repeated authentication failures.",
            "Mandate public key authentication or MFA for SSH/FTP administration endpoints.",
            "Isolate target authentication service behind an encrypted bastion host / VPN."
        ]
    },
    3: {
        "stage_name": "Denial of Service",
        "tactic_id": "TA0040",
        "tactic_name": "Impact",
        "technique_id": "T1498",
        "technique_name": "Network Denial of Service (DoS / DDoS)",
        "description": "Extreme surges in packet rate and connection volume threatening network resource exhaustion and service disruption.",
        "severity": "CRITICAL",
        "mitigations": [
            "Activate upstream DDoS scrubbing center traffic redirection.",
            "Enable kernel-level SYN cookies and aggressive TCP connection timeout parameters.",
            "Rate-limit ingress border routers based on anomalous flow volume."
        ]
    },
    4: {
        "stage_name": "Exploitation / Initial Access",
        "tactic_id": "TA0001",
        "tactic_name": "Initial Access",
        "technique_id": "T1190",
        "technique_name": "Exploit Public-Facing Application",
        "description": "Anomalous packet lengths and asymmetric payload distributions indicative of application vulnerability exploitation.",
        "mitigations": [
            "Inspect Web Application Firewall (WAF) inspection logs for malicious request signatures.",
            "Apply virtual patch rules on reverse proxies for exposed web services.",
            "Quarantine suspect backend application containers pending memory inspection."
        ]
    }
}


class MitreMapper:
    """
    Translates model predictions and state telemetry into MITRE ATT&CK intelligence.
    """

    @staticmethod
    def map_stage_to_mitre(
        stage_id: int,
        risk_score: float = 0.0,
        physical_metrics: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Maps stage ID and physical metrics to MITRE ATT&CK metadata.

        Args:
            stage_id: Integer stage code (0 to 4).
            risk_score: Predicted future risk score in [0, 1].
            physical_metrics: Dictionary of predicted physical metrics (flows, ports, etc.).

        Returns:
            Dictionary containing MITRE ATT&CK tactic, technique, and defensive mitigations.
        """
        base_intel = MITRE_TACTIC_DATABASE.get(stage_id, MITRE_TACTIC_DATABASE[0]).copy()

        # Dynamic nuance based on physical metrics
        if physical_metrics:
            ports = physical_metrics.get("unique_dst_ports", 0)
            flows = physical_metrics.get("flow_count", 0)
            syn = physical_metrics.get("syn_flag_count", 0)

            # Refine Reconnaissance if broad port scan
            if stage_id == 1 and ports > 100:
                base_intel["technique_name"] = "Broad Spectrum Port Scan (Horizontal/Vertical)"
                base_intel["description"] += f" Observed extensive port exploration ({ports} unique destination ports)."

            # Refine Credential Access if high velocity
            if stage_id == 2 and flows > 1000:
                base_intel["technique_name"] = "High-Velocity Password Spraying / Brute Force"
                base_intel["description"] += f" High transaction velocity ({flows:,} flows/min) targeting authentication services."

        # Confidence rating derived from risk score
        confidence = "HIGH" if risk_score > 0.70 else ("MEDIUM" if risk_score > 0.35 else "LOW")
        base_intel["confidence"] = confidence
        base_intel["associated_risk_pct"] = round(risk_score * 100, 1)

        return base_intel

    @classmethod
    def map_trajectory_progression(
        cls,
        current_state_info: Dict[str, Any],
        forecast_timeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Builds a comprehensive tactical progression timeline connecting:
        1. Observed state behaviour S(t)
        2. Predicted future tactical stages S(t+1) ... S(t+K)

        Args:
            current_state_info: Current state dictionary containing stage_id, risk_score,
                                physical_metrics, and timestamp.
            forecast_timeline: Multi-step forecast list from KStepSimulator.

        Returns:
            List of chronological progression items for rendering in the MITRE view.
        """
        progression = []

        # 1. Observed Current State
        cur_stage = current_state_info.get("stage_id", 0)
        cur_risk = current_state_info.get("risk_score", 0.0)
        cur_phys = current_state_info.get("physical_metrics", {})
        cur_time = current_state_info.get("timestamp", "Current Time")

        cur_intel = cls.map_stage_to_mitre(cur_stage, cur_risk, cur_phys)
        ports = int(cur_phys.get("unique_dst_ports", 0))
        flows = int(cur_phys.get("flow_count", 0))
        pkt_rate = float(cur_phys.get("packet_rate", 0.0))

        progression.append({
            "type": "OBSERVED",
            "step_label": "Current Observed State S(t)",
            "timestamp": str(cur_time),
            "stage_id": cur_stage,
            "stage_name": cur_intel["stage_name"],
            "tactic_id": cur_intel["tactic_id"],
            "tactic_name": cur_intel["tactic_name"],
            "technique_id": cur_intel["technique_id"],
            "technique_name": cur_intel["technique_name"],
            "severity": cur_intel["severity"],
            "confidence": "OBSERVED TELEMETRY",
            "risk_pct": round(cur_risk * 100.0, 1) if cur_risk <= 1.0 else round(cur_risk, 1),
            "description": cur_intel["description"],
            "behavioral_indicators": (
                f"Observed Flow Volume: {flows:,} | Target Ports: {ports} | "
                f"Packet Velocity: {pkt_rate:.1f} pkts/s"
            ),
            "mitigations": cur_intel["mitigations"]
        })

        # 2. Predicted Future Trajectory Steps
        for item in forecast_timeline:
            fut_stage = item.get("predicted_stage_id", 0)
            fut_risk = item.get("predicted_risk_pct", 0.0) / 100.0
            fut_phys = item.get("physical_metrics", {})
            fut_step = item.get("step", "t+1")
            fut_min = item.get("minutes_ahead", 1)

            fut_intel = cls.map_stage_to_mitre(fut_stage, fut_risk, fut_phys)
            f_ports = int(fut_phys.get("unique_dst_ports", 0))
            f_flows = int(fut_phys.get("flow_count", 0))
            f_rate = float(fut_phys.get("packet_rate", 0.0))

            progression.append({
                "type": "PREDICTED",
                "step_label": f"Projected Step {fut_step} (+{fut_min} min)",
                "timestamp": f"+{fut_min}m from S(t)",
                "stage_id": fut_stage,
                "stage_name": fut_intel["stage_name"],
                "tactic_id": fut_intel["tactic_id"],
                "tactic_name": fut_intel["tactic_name"],
                "technique_id": fut_intel["technique_id"],
                "technique_name": fut_intel["technique_name"],
                "severity": fut_intel["severity"],
                "confidence": fut_intel["confidence"],
                "risk_pct": round(fut_risk * 100.0, 1),
                "description": fut_intel["description"],
                "behavioral_indicators": (
                    f"Simulated Flow Volume: {f_flows:,} | Target Ports: {f_ports} | "
                    f"Projected Rate: {f_rate:.1f} pkts/s"
                ),
                "mitigations": fut_intel["mitigations"]
            })

        return progression

