# Intel — Persistent Memory

> This file is read at the start of each run and updated after each ticket processed.
> It enables continuous improvement of analyses over time.

## Patterns by Sector

- **Agri-food / Industrial maintenance** : mostly physical tasks (on-site visits, repairs, diagnostics), only reports and GMAO partially automatable. Typical rate: 20-30% → always SKIP.
- **Off-target offers** : Scout sometimes surfaces maintenance-related offers via search term "assistant ADV". These are systematically SKIP.

## Validated Approach Angles (go by client)

_No angles recorded yet._

## Rejected Angles (skip by client)

_No angles recorded yet._

## Average Automation Rates by Job Type

| Job Type | Rate | Date |
|-----------|------|------|
| Industrial maintenance apprentice | 25% | 2026-04-03 |
| Commercial apprenticeship (e-learning) | 40% | 2026-04-05 |
| Digital CFA admin assistant | 81% | 2026-04-05 |

## Companies Already Analyzed

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Company A (food & agriculture, 1500 emp) | Agri-food | skip | 2026-04-03 |
| Company B (online training, 289 emp) | Online education | skip | 2026-04-05 |
| Company C (digital CFA, 1-2 emp) | Digital CFA | go | 2026-04-05 |

## Learned Lessons

- Company A: Large group with 1500 employees, 412M€ revenue, subsidiary of international pharmaceutical company. Email domains without MX. Prospection not feasible.
- Large companies (>200 emp) that are subsidiaries of groups = decision chain too long for solo freelancer.
- Company B: Subsidiary created 2020, 289 employees, commercial role = minimal ADV → skip.
- Company C: Digital CFA created 2020, 1-2 employees, 878k€ revenue. Management of OPCO + apprenticeship contracts = highly automatable (81%).
- Training with Ypareo software (CFA ERP) = opportunity for n8n integration to automate data entry.
- Domains without confirmed MX: include best_guess anyway, system handles missing recipient.
- Offers through recruitment agencies without identified final employer = cancel immediately.
- Public entities, large groups (>70k employees), large protection/insurance groups = always off-target.

## Automation Rates by Job Type (continued)

| Job Type | Rate | Date |
|-----------|------|------|
| Commercial via recruitment agency | N/A (cancel) | 2026-04-05 |

## Companies Already Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Home Services Org (domestic help, region) | Home services | cancel | 2026-04-05 |
| Municipal Government Office | Public sector | cancel | 2026-04-05 |
| Large Construction Group | BTP/Energy mega-group | cancel | 2026-04-05 |
| Large Protection Org | Protection/Insurance mega-group | cancel | 2026-04-05 |
| Recruitment Cabinet (ENR) | HR cabinet without employer identified | cancel | 2026-04-05 |

## Update 2026-04-05 (run TEI-105)

- Each ticket has its own dedicated run → impossible to process multiple tickets per heartbeat (checkout conflict 409 on all others).

## Update 2026-04-05 (run TEI-101)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Medical/Publishing Group | Medical conferences / Health publishing (PE-backed) | skip | 2026-04-05 |

### Learned Lessons (continued)

- Medical Publishing Group: 420 employees, 123M€ revenue, controlled by PE fund since June 2024. New management appointed by fund. Target: 2x growth in 5 years → hiring, not freelance. Off-target even with 56% automation rate.
- Companies under PE control (investment funds) = decision chain too long, even if CEO identified → Skip systematically.
- Company domains without MX, probable emails on alternative domain.

## Update 2026-04-05 (run TEI-100)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Company D (technical consulting, 150 emp) | O&G/Nuclear/Life Sciences Engineering | go | 2026-04-05 |

### Patterns by Sector (continued)

- **Technical consulting O&G/Nuclear** : ADV = timesheet billing → highly automatable invoicing. ADP = absence/training/medical visit tracking = automatable. Typical rate: 75-80%.
- **Email domain discovery** : scripts may search primary domain but active domain may differ → always verify via ZoomInfo/web if MX doesn't respond.
- **Minority PE (<20%)** : doesn't block prospection if founders identifiable and publicly accessible (≠ majority PE = skip).

### Automation Rates (continued)

| Job Type | Rate | Date |
|-----------|------|------|
| ADP/ADV assistant technical consulting | 77% | 2026-04-05 |

### Learned Lessons (continued)

- Company D: 150 employees, 83M€ revenue 2024, minority PE stake 15%. Co-founders still operational via personal holdings. Founder accessible. Email best guess: prenom.nom@domain.fr.
- When formal director = legal entity (holding), search for physical founder behind it — often accessible via LinkedIn/press.

## Update 2026-04-05 (run TEI-99)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Company E (Asian food wholesale, region) | Asian food wholesale in growth | go | 2026-04-05 |

### Patterns by Sector (continued)

- **Growing Asian food wholesale** : order entry + packing lists + follow-up = core ADV highly automatable. Typical rate: 75%.
- Holding as SAS President = search for physical founder behind holding (founder name identifiable).
- Company domain without confirmed MX — best_guess included.

### Automation Rates (continued)

| Job Type | Rate | Date |
|-----------|------|------|
| ADV assistant food wholesale | 75% | 2026-04-05 |

### Learned Lessons (continued)

- Company E: 9 employees, founded 2023, 100k€ net profit. Hiring first ADV to absorb client growth. Founder identifiable. Email : prenom.nom@domain.fr (no MX).
- Very small structures in growth (<10 emp) = ideal target if founder identifiable.

## Update 2026-04-05 (run TEI-110)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Company F (accounting cabinet, region) | Accounting / CPA firm (family SA) | go | 2026-04-05 |

### Patterns by Sector (continued)

- **Traditional accounting cabinet (family SA)** : Sage data entry + reconciliation + follow-up + calendars + tax deadlines = highly automatable. Typical rate: 75-80%.
- Pre-1990 cabinets without own website = ISP emails (neuf.fr, wanadoo.fr) → verify on professional directories.
- Sage = accounting cabinet software, API available → n8n integration medium complexity.

### Automation Rates (continued)

| Job Type | Rate | Date |
|-----------|------|------|
| Admin & accounting assistant cabinet | 77% | 2026-04-05 |

### Learned Lessons (continued)

- Company F: Family SA 1975, 10-19 employees, director identifiable. Email : prenom.nom@isp.fr (directories, score 55). No own domain. Cabinet email: contact.cabinet@isp.fr.
- For traditional cabinets without website: search professional accountant directories → ISP emails often found there.

## Update 2026-04-05 (run TEI-113)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Company G (IT consulting, 3-5 emp) | IT systems consulting (SAS, 3-5 emp) | go | 2026-04-05 |

### Patterns by Sector (continued)

- **Small tech/IT consulting PME (<10 emp)** : sales pipeline (quotes + follow-up + CRM) highly automatable. Typical rate: 70-75%. Tech-savvy profile = automation pitch well received.

### Automation Rates (continued)

| Job Type | Rate | Date |
|-----------|------|------|
| Commercial assistant small tech PME | 72% | 2026-04-05 |

### Learned Lessons (continued)

- Company G: SAS 2020, 3-5 employees, web/mobile/chatbot specialty region. Company domain without MX. Email best_guess : prenom.nom@company.fr (score 55).
- For directors with only surname in registry: always search for first name via web before running email-finding script.

## Update 2026-04-05 (run TEI-114)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Anonymous via Agency | Medical region (confidential) | cancel | 2026-04-05 |

### Learned Lessons (continued)

- Recruitment agencies often post offers for confidential clients: "we are recruiting on behalf of our client, a company in the medical sector". Employer not identifiable = cancel immediately.
- Major recruitment agencies = often anonymous employer in LinkedIn post → always verify before analyzing.

## Update 2026-04-07 (run TEI-117)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Company H (real estate, 7 agencies region) | Real estate agencies, 7 locations | skip | 2026-04-07 |

### Patterns by Sector (continued)

- **Real estate rental agent** : field role (visits, inspection reports, work follow-up). Off-target systematically. Rate ~33%.
- **"Real estate agent" offers** : search term surfaces field roles — skip systematically.

### Automation Rates (continued)

| Job Type | Rate | Date |
|-----------|------|------|
| Real estate rental agent | 33% | 2026-04-07 |

## Update 2026-04-07 (run TEI-118)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Hypermarket Chain Member | Hypermarket (independent franchise member) | cancel | 2026-04-07 |

### Learned Lessons (continued)

- Hypermarket chain members = 100-500 employees → always off-target even if legally independent.
- "COMEX ASSISTANT" role (executive committee) = executive assistant, not ADV → off-target.
- These offers via real estate search term = always off-target systematically.

## Update 2026-04-07 (run TEI-119)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Large Recruitment Cabinet (real estate) | Recruitment cabinet + field | cancel | 2026-04-07 |

### Learned Lessons (continued)

- Large international recruitment cabinet = off-target. "Real estate agent" offers via large cabinet = double off-target (unknown employer + field role).
- "Agent" via cabinet = always cancel (anonymous employer + field).

## Update 2026-04-07 (run TEI-121)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Company B (2nd offer) | Online training / Apprenticeship management | cancel | 2026-04-07 |

### Learned Lessons (continued)

- Company B = always cancel (already off-target, 289 employees, training subsidiary). Regardless of role.

## Update 2026-04-07 (run TEI-122)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Business School (region) | Business school (Galileo Global Education group) | cancel | 2026-04-07 |

### Learned Lessons (continued)

- Business school = large education group (mega-group). "Polyvalent assistant" role = student admin, not ADV. Off-target even if small campus size.
- Business schools (commerce schools, etc.) = always off-target (educational group >200 emp, long decision chain).

## Update 2026-04-07 (run TEI-123)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Commercial Network | Sales school / independent commercial networks | cancel | 2026-04-07 |

### Learned Lessons (continued)

- Independent commercial network = field role with travel. "Real estate negotiator" search surfaces non-ADV commercial offers → off-target systematically.

## Update 2026-04-07 (run TEI-124)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Large Auto Distributor | Auto distribution (multiple brands, 400+ emp) | cancel | 2026-04-07 |

### Learned Lessons (continued)

- Large auto distributor = 400+ employees, multi-brand. Used car sales role = field role, zero ADV automation → cancel.
- "Real estate negotiator" search also surfaces auto sales field offers → double off-target systematically.

## Update 2026-04-07 (run baade351 / TEI-125 + TEI-126)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Auto Concessionaire | Auto dealer (used car sales field) | cancel | 2026-04-07 |
| Large Mutual Insurance | Large mutual insurance group (national) | cancel | 2026-04-07 |

### Learned Lessons (continued)

- Auto concessionaire = used car sales field role, 0% ADV. Same pattern as large auto distributor.
- Large mutual insurance = national mega-group. Commercial advisor field role (insurance/pension) = off-target. Same pattern as large protection groups.
- "Real estate negotiator" search = systematically surfaces: real estate field agents, used car sellers, insurance commercial advisors → ALL off-target.

## Update 2026-04-07 (run TEI-127)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Large Food Distribution Group | Food distribution mega-group (5000+ emp, billions revenue) | cancel | 2026-04-07 |

### Learned Lessons (continued)

- Food distribution mega-group = very large (thousands of employees, billions revenue). Even if subsidiary = off-target due to long decision chain.
- Large food distributors (national/multi-billion) = cancel systematically even for sedentary roles.

## Update 2026-04-07 (run TEI-128)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Real Estate Agency | Real estate (field negotiator) | cancel | 2026-04-07 |

### Learned Lessons (continued)

- Real estate agency = field negotiator role, 0% ADV → cancel.
- Online CFA = posts apprenticeship offers for host companies. Employer unknown → cancel systematically.
- Online commerce school = likely CFA or business school (national, online training). Offer = probably CFA or large school → off-target → cancel.
- Online CFAs (various names) = always cancel, final employer not identifiable.

### Patterns by Sector (continued)

- **Online CFAs** : post apprenticeship offers for client companies. Final employer unknown → cancel immediately.

## Update 2026-04-07 (run TEI-131)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Company I (training org, 20-49 emp) | Adult continuing education / HR consulting (region) | maybe | 2026-04-07 |

### Patterns by Sector (continued)

- **Qualiopi-certified training org** : training files + attendance + certificates highly automatable, but physical reception and field logistics weigh. Typical rate: 50%. Maybe only.
- **Multi-entity group** : training org + HR recruitment. Same governance and management structure.

### Automation Rates (continued)

| Job Type | Rate | Date |
|-----------|------|------|
| Commercial assistant training org (Qualiopi) | 50% | 2026-04-07 |

### Learned Lessons (continued)

- Company I: 20-49 employees, director identifiable. Email pattern: prenom.nom@group-domain.fr (verified via other company employees). Domain without MX.
- Online CFA = always cancel confirmed (CFA online, final employer unknown).

## Update 2026-04-08 (run TEI-135)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Private Hospital (regional) | Healthcare / Private hospital (national group) | cancel | 2026-04-08 |

### Learned Lessons (continued)

- Private hospital = national healthcare mega-group. Hospital admin role = strong regulatory constraints + long decision chain → cancel systematically.
- "Real estate agent" search also surfaces healthcare admin offers → off-target.

## Update 2026-04-08 (run TEI-136)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Real Estate Network Agency | Real estate (transaction advisor) | cancel | 2026-04-08 |

### Learned Lessons (continued)

- Real estate network agency = 14 employees. Role: transaction advisor (field VRP/commercial). Field only = 0% ADV. Same pattern as others.
- "Real estate negotiator" continues to surface field roles → always cancel.

## Update 2026-04-08 (run TEI-137)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Large Auto Group | Multi-brand auto dealerships (44 locations, region) | cancel | 2026-04-08 |

### Learned Lessons (continued)

- Large auto group = 44 dealerships region. Apprentice commercial advisor = field only (showroom, prospecting), 0% ADV. Double off-target.
- "Real estate negotiator" search confirmation: always surfaces field roles (real estate, auto, insurance) → cancel systematically.

## Update 2026-04-08 (run TEI-138)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Large BTP Group | BTP/Industrial envelope (ETI 2000-4999 emp) | cancel | 2026-04-08 |

### Learned Lessons (continued)

- Large BTP group = ETI 2000-4999 employees, no job description available. Triple off-target.
- "Real estate negotiator" search → surfaces large groups without description = off-target systematically.

## Update 2026-04-09 (run TEI-140/141/142/143)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Global Real Estate Services | Real estate services mega-group (>100k emp) | cancel | 2026-04-09 |
| Large Auto Group (2nd offer) | Auto distribution, used vehicle field role | cancel | 2026-04-09 |
| Banking Subsidiary Real Estate | Real estate subsidiary of bank (mega-group) | cancel | 2026-04-09 |
| Sports Sponsorship App | Sponsorship app startup, commercial field role | cancel | 2026-04-09 |

### Learned Lessons (continued)

- Global real estate mega-group → always cancel even for admin roles.
- Large auto group continues posting field offers → cancel systematically on all new offers.
- Banking subsidiary real estate = VRP field real estate, 0% ADV.
- Sports app startup = commercial field apprentice (sports clubs) = 0% ADV. "Real estate negotiator" search → another false positive.
- Large auto group = always cancel on any new offer.

## Update 2026-04-09 (run TEI-144/145)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Telecom/Fiber Company | Telecom / Fiber optics (commercial field) | cancel | 2026-04-09 |
| Technical Inspection Bureau | Technical inspection mega-group (~12k emp) | cancel | 2026-04-09 |

### Learned Lessons (continued)

- Telecom company = fiber/telecom commercial advisor region, pure field prospecting = 0% ADV. "Real estate negotiator" search → always surfaces commercial field false positives.
- Technical inspection mega-group = national mega-group (~12,000 employees), no description. "Operations assistant" = field operations support. Same pattern as large BTP groups → cancel systematically.
- "Real estate negotiator" search generates almost exclusively false positives: field real estate, auto used vehicle sales, insurance, telecom field, mega-groups. Very few actual ADV/admin offers.

## Update 2026-04-10 (run TEI-147)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Business School | Business school / BTS apprenticeship program | cancel | 2026-04-10 |

### Learned Lessons (continued)

- Business school = private commerce school, posts BTS apprenticeship offers. Same pattern as other educational groups (long decision chain). No job description available. Double off-target.
- "Real estate agent" continues to surface: business schools, field real estate agents, auto dealerships. Almost 0% valid ADV/admin offers.

## Update 2026-04-10 (run TEI-148)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Finance & Real Estate Company | Financial services auxiliary / real estate (SARL 0 emp) | cancel | 2026-04-10 |

### Learned Lessons (continued)

- Finance company = unipersonal SARL, 0 employees. Director "name only" in registry. "Real estate agent" via search = field only, 0% ADV. Cancel systematically.
- "Real estate agent" search confirmation: 100% of analyzed offers = field role, mega-group, or non-ADV role. This search term produces NO valid targets.

## Update 2026-04-10 (run TEI-149)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Real Estate Agency Network | Real estate (field negotiator) | cancel | 2026-04-10 |

### Learned Lessons (continued)

- Real estate network agency = field negotiator role, 0% ADV → cancel. Same pattern as others.

## Update 2026-04-10 (run TEI-150)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Real Estate Agency | Real estate (field advisor, region) | cancel | 2026-04-10 |

### Learned Lessons (continued)

- Real estate agency = field advisor (prospecting, negotiation, contracts). 0% ADV → cancel. Same pattern.
- "Real estate negotiator" search confirmation: 100% of analyzed offers = field real estate, auto sales, insurance, telecom. This search term produces NO valid ADV targets.

## Update 2026-04-10 (run TEI-151)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Temp Agency | Temp work (SAS, 50-99 emp) | cancel | 2026-04-10 |

### Learned Lessons (continued)

- Temp agency = temporary staffing, 50-99 employees. Only directors as legal entities (no physical person identifiable). Prospection impossible.
- "Executive assistant" role = executive support (calendars/travel/expenses) ≠ ADV. Off-target even if director identified.
- Temp agencies posting on industry job boards = double off-target (sector + role).

## Update 2026-04-11 (run TEI-153)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Real Estate Network | Real estate (independent advisor, region) | cancel | 2026-04-11 |

### Learned Lessons (continued)

- Real estate network = independent advisors (pure field). 0% ADV + independent status = double off-target.
- "Real estate agent" search → pattern 100% confirmed: all offers = field real estate, auto sales, insurance, telecom. No valid ADV targets.

## Update 2026-04-11 (run TEI-154)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Consulting & HR Cabinet | Consulting/recruitment cabinet (SAS, 3-5 emp) | cancel | 2026-04-11 |

### Learned Lessons (continued)

- HR Cabinet: SAS 2019, 3-5 employees. President = only legal entity (no physical person). No identifiable director. Domain = empty. Cancel.
- HR/consulting cabinets with holding as president = cancel immediately (same pattern as temp agencies).

## Update 2026-04-11 (run TEI-156)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| Company J (real estate development, ~20 emp) | VEFA real estate development (small structure) | go | 2026-04-11 |

### Patterns by Sector (continued)

- **VEFA real estate development (small structure)** : reservations + SRU contracts + notary follow-up + CRM = core ADV highly automatable. Typical rate: 75-80%.
- **Multi-entity structure** : all subsidiaries at same headquarters. Independent group ~20 employees.
- **"Real estate negotiator" search** can also surface legitimate ADV roles (commercial assistant VEFA real estate development) → analyze description before canceling.

### Automation Rates (continued)

| Job Type | Rate | Date |
|-----------|------|------|
| Commercial assistant VEFA real estate development | 78% | 2026-04-11 |

### Learned Lessons (continued)

- Company J = VEFA real estate development, co-founders identifiable, tech-receptive profile.
- Legal entity names may differ from employer entity (different subsidiary mentioned in legal notices).

## Update 2026-04-11 (run TEI-157)

### Companies Analyzed (continued)

| Company | Sector | Verdict | Date |
|-----------|---------|---------|------|
| National Real Estate Developer | VEFA real estate national (ETI, region) | cancel | 2026-04-11 |

### Learned Lessons (continued)

- National real estate developer = national ETI, hundreds of entities, mega-auditor. "VEFA commercial advisor" = sales/negotiation (70-100k€ commission), not ADV. Double off-target.
- "Real estate negotiator" search also surfaces "VEFA commercial advisor" at large developers → always check group size before analyzing.
- Same offer type "VEFA" can be legitimate (Company J: small PME) or off-target (national ETI) → company size is deciding factor.
