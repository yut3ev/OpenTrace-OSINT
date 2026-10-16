interface PrivacyTermsPageProps {
  onBackToConsole: () => void;
}

export function PrivacyTermsPage({ onBackToConsole }: PrivacyTermsPageProps) {
  return (
    <div className="doc-page">
      <div className="doc-header">
        <button className="btn-secondary btn-sm" onClick={onBackToConsole}>
          ← Back to Console
        </button>
        <h1>Ethics, Privacy Policy & Terms of Use</h1>
        <p className="doc-subtitle">
          Guidelines, legal protections, and responsible disclosure standards for the OpenTrace OSINT platform.
        </p>
      </div>

      <div className="doc-section">
        <h2>1. Ethical OSINT Framework</h2>
        <p>
          OpenTrace is built strictly for legitimate security analysis, defensive threat intelligence,
          fraud prevention, and identity verification. The software adheres to the following principles:
        </p>
        <ul>
          <li><strong>Public Sources Only:</strong> The platform only queries publicly accessible endpoints, open registries, and public search engines.</li>
          <li><strong>No Authentication Bypass:</strong> OpenTrace never circumvents login barriers, captcha mechanisms, or access-control lists.</li>
          <li><strong>No Dark Web or Data Breaches:</strong> Default installations avoid underground breach dumps and unverified credentials.</li>
          <li><strong>Rate Limiting & Politeness:</strong> Requests respect target server load through bounded concurrency and polite user-agent identification.</li>
        </ul>
      </div>

      <div className="doc-section">
        <h2>2. Privacy & Data Isolation Policy</h2>
        <p>
          We believe research data belongs solely to the researcher who generated it:
        </p>
        <ul>
          <li><strong>Strict Ownership Isolation:</strong> User investigations are cryptographically and relationally isolated. No user can discover, enumerate, or inspect another user's research.</li>
          <li><strong>Zero Cross-Tenant Leakage:</strong> Queries, findings, and targets are never pooled into a shared analytics database or used for profiling.</li>
          <li><strong>Right to Erasure:</strong> When an investigation or user account is deleted, all associated findings, logs, and reset tokens are immediately removed from storage.</li>
          <li><strong>Anti-Enumeration Safeguards:</strong> Attempting to query an investigation owned by another account returns an ambiguous <code>404 Not Found</code> error to prevent ID probing.</li>
        </ul>
      </div>

      <div className="doc-section">
        <h2>3. Acceptable Use Policy</h2>
        <p>
          By accessing OpenTrace, users agree not to use the platform for any unlawful, abusive, or harmful purposes, including:
        </p>
        <ul>
          <li>Stalking, harassment, or unauthorized surveillance of individuals</li>
          <li>Malicious doxxing or publication of private personal data</li>
          <li>Automated scraping designed to degrade third-party service availability</li>
          <li>Violation of international or domestic privacy laws (e.g., GDPR, CCPA, HIPAA)</li>
        </ul>
      </div>

      <div className="doc-section">
        <h2>4. Disclaimer of Liability</h2>
        <p>
          OpenTrace is provided as open-source software under the Apache 2.0 license. In no event shall
          the contributors or hosting providers be liable for any direct, indirect, incidental, or consequential
          damages arising out of the use or inability to use this software. Users are solely responsible for ensuring
          their investigative activities comply with all applicable local, national, and international laws.
        </p>
      </div>
    </div>
  );
}
