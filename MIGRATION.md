# Morty™ Rebrand & Migration Guide

This guide helps maintainers and users understand what changed during the Morty rebrand, what stayed the same, and how to reference the upstream Snappy project. The collaboration with Vultr is **pro-bono**; no compensation or sponsorship was exchanged.

## What Changed

- Documentation, screenshots, and badges now reference Morty instead of Snappy.  
- New legal pages: `TRADEMARKS.md` and `LICENSES/SNAPPY_MIT_LICENSE.txt`.  
- Updated copy highlights the Vultr collaboration and Morty™ trademark usage.  
- Redirect map (`docs/redirects.md`) captures slug updates for documentation sites.  
- README and architecture docs display the required rebrand notice.  
- Docker Compose network renamed to `morty-network`; update local overrides or deployment scripts that referenced `snappy-network`.

## What Did Not Change

- APIs, CLI flags, environment variables, and SDK shapes.  
- File paths and configuration schema identifiers.  
- Licensing terms: the codebase remains under the MIT License.

## Licensing & Attribution

- The upstream Snappy project is MIT-licensed; the full text is reproduced in `LICENSES/SNAPPY_MIT_LICENSE.txt`.  
- Upstream copyright notices stay untouched.  
- Morty documentation references Snappy and links to https://github.com/athrael-soju/Snappy.

## Compensation Disclosure

The Morty rebrand and related promotional materials are provided **pro-bono**. Vultr supplied branding assets and review support only.

## Compatibility

- Existing Snappy deployments can pull the Morty docs without code changes.  
- All references to Snappy-ranked tooling in code or configuration remain valid.  
- When showcasing Morty, acknowledge that it is based on the Snappy project and licensed under MIT.

## FAQ

**Is Morty affiliated with Vultr?**  
Morty is a collaborative, pro-bono promotion featuring Vultr’s Morty™ mascot. Vultr retains trademark ownership and provides brand guidelines; there is no financial sponsorship.

**How should I cite Snappy?**  
Reference the upstream repository (https://github.com/athrael-soju/Snappy) and include the MIT License attribution preserved in this repo.

**Where is the upstream code?**  
Snappy’s history and ongoing development live at https://github.com/athrael-soju/Snappy. Morty tracks upstream changes via standard Git workflows.

**Is this a paid promotion?**  
No. The collaboration is **pro-bono**. Morty documentation calls this out explicitly on every page.

**Are code identifiers changing?**  
No. Package names, environment variables, and CLI commands keep their Snappy-prefixed identifiers to avoid breaking existing automation.

**Can I continue using Snappy docs?**  
Yes. Morty documentation remains compatible and cross-links to upstream resources where appropriate.

---

Morty is a rebrand based on the open-source project Snappy (https://github.com/athrael-soju/Snappy). Portions are licensed under the **MIT License**; license and attribution preserved.
