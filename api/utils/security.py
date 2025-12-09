

def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "***"

    local, domain = email.split("@", 1)
    if not domain:
        return "***"

    parts = domain.split(".")
    if len(parts) < 2:
        # no real tld – mask simply
        l_shown = local[:3]
        l_masked = "*" * max(len(local) - 3, 0)
        d_shown = domain[:3]
        d_masked = "*" * max(len(domain) - 3, 0)
        return f"{l_shown}{l_masked}@{d_shown}{d_masked}"

    tld = parts[-1]                 # "com"
    domain_name = ".".join(parts[:-1])  # "example" or "example.co"

    l_shown = local[:3]
    l_masked = "*" * max(len(local) - 3, 0)

    d_shown = domain_name[:3]
    d_masked = "*" * max(len(domain_name) - 3, 0)

    return f"{l_shown}{l_masked}@{d_shown}{d_masked}.{tld}"
