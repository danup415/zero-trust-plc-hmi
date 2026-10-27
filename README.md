# Zero Trust PLC-HMI Security
# Zero Trust Architecture for PLC-HMI Security

A cybersecurity project demonstrating a Zero Trust approach to securing communication between Programmable Logic Controllers (PLCs) and Human-Machine Interfaces (HMIs) in Industrial Control Systems (ICS).

## Overview

Traditional industrial control systems often rely on trusted internal networks. This project explores how Zero Trust principles can strengthen PLC-HMI communication by verifying requests, enforcing access controls, and monitoring potentially malicious activity.

The project includes a PLC simulation, a security proxy, an HMI client, a SCADA dashboard, and attack simulation scripts for security testing in a controlled environment.

## Objectives

- Demonstrate Zero Trust principles in industrial automation.
- Secure PLC-HMI communication through a proxy-based architecture.
- Simulate common attack scenarios in a test environment.
- Monitor system activity and visualize tank status.
- Explore security controls for industrial control systems.

## Project Architecture

The system is organized into the following components:

1. **PLC Simulation (`plc/`)** — Contains the PLC program for the simulated process.
2. **Security Proxy (`proxy/`)** — Contains the proxy and HMI client components used in PLC-HMI communication.
3. **Attack Simulations (`attacks/`)** — Contains scripts for testing security against selected attack scenarios.
4. **SCADA Dashboard (`dashboard/`)** — Contains the dashboard interface and SCADA bridge.
5. **HMI (`hmi/`)** — Reserved for HMI-related components.
6. **Certificates (`certs/`)** — Contains certificate-generation resources.
7. **Monitoring (`monitoring/`)** — Reserved for monitoring components.
8. **Scripts (`scripts/`)** — Contains startup, setup, and tank-monitoring scripts.
9. **Documentation (`docs/`)** — Reserved for project documentation.

## Security Testing

The attack simulation scripts cover scenarios such as:

- Valve manipulation
- Request spoofing
- Tank draining
- Replay attacks
- System reset behavior

These scripts are intended for authorized testing within the isolated simulation environment.

## Technology Stack

- Python
- Structured Text (IEC 61131-3)
- PLC simulation
- HMI and SCADA concepts
- Git and GitHub
- Certificate-based security components

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/danup415/zero-trust-plc-hmi.git
cd zero-trust-plc-hmi
```

### 2. Review the project files

Inspect the PLC program, proxy scripts, dashboard, attack simulations, and setup instructions before running the system.

### 3. Configure the environment

Review the scripts in `scripts/` and the certificate-generation resources in `certs/`. Follow the applicable setup instructions for your local PLC simulation environment.

### 4. Run the simulation

Use the appropriate startup scripts and configuration for your environment. Test attack scenarios only within the isolated, authorized lab setup.

**Note:** Exact installation commands, dependencies, network ports, and execution order should be documented after validating the current project configuration.

## Safety and Security

- Run attack simulations only in an isolated, authorized test environment.
- Never expose a real PLC or industrial control system to unvalidated attack scripts.
- Do not commit private keys, passwords, access tokens, or production credentials.
- Review certificate handling and access-control configuration before deployment.
- This project is intended for educational and research purposes and is not, by itself, evidence of production-ready industrial security.

## Future Improvements

- Add comprehensive authentication and authorization tests.
- Document the security proxy's request-validation workflow.
- Add audit logging and monitoring metrics.
- Include reproducible security evaluation results.
- Document deployment architecture and known limitations.

## Author

**Anup Deshmukh**

GitHub: [@danup415](https://github.com/danup415)

## License

A license has not yet been specified. All rights remain with the respective copyright holders until a license is added.
