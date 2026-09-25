#!/usr/bin/env python3
"""Parse Blair's ATS HTML and portfolio index into normalized graph.json."""
from pathlib import Path
import json, re
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"
OUT = ROOT / "data" / "graph.json"

DOMAINS = {
    "Cloud & Infrastructure": ["AWS","OpenStack","UpCloud","Rackspace","Liquid Web","Nexcess","AWS RDS","DynamoDB","Redshift","CloudFront","AWS EMR","S3","HDFS"],
    "Linux & Systems": ["Linux","Red Hat","RHCE6","RHCSA6","CentOS","Ubuntu","Windows Server","Apache","NGINX","IIS/.NET","cPanel","Plesk","InterWorx","Virtualmin","SSH","FTP","DNS","TCP/IP","SSL/TLS"],
    "Databases & Data": ["MySQL","MariaDB","Percona Server","Percona XtraDB Cluster","PXC","Galera","PostgreSQL","MongoDB","SQLite","Redis","Elasticsearch","HAProxy","Varnish","PMM","HiveQL","Hadoop"],
    "DevOps & Automation": ["Docker","Docker Swarm","Kubernetes","Terraform","Ansible","Puppet","Chef","Git","CI/CD","Infrastructure as Code","IaC","Cron","WP-CLI"],
    "Web & E-commerce": ["WordPress","WooCommerce","Magento","Drupal","Joomla","Django","Node.js","PHP","JavaScript","REST APIs","Webhooks","Headless architecture","LAMP","LEMP"],
    "Observability & Security": ["Nagios","Datadog","Splunk","Prometheus","Grafana","Nessus","Metasploit","Wireshark","MTR","Traceroute","Nmap","Cloudflare","PCI-DSS","OWASP"],
    "Enterprise & Support": ["L3 Support","Managed Applications","Technical Account Management","TAM","Solutions Consulting","Technical Support","Pre-Sales Engineering","Solution Architecture","Incident Response","SLA","Enterprise Support","Customer Success"],
    "Product & Business": ["Product Management","Product Manager","Roadmap Planning","Agile","UX/UI","Front-End Modernization","Technical Sales","Consultative Selling","Inventory","Retail","Event Operations","Experiential Marketing","Visual Merchandising","Customer Engagement"],
    "Programming & Engineering": ["Python","Go","Golang","C/C++","Lua","SQL","Bash","Full Stack Development","Front-End Development","API Integrations","Microservices"],
    "Credentials & Education": ["AWS Cloud Practitioner","AWS Solutions Architect Associate","RHCE","RHCSA","BSBA","ASBA","MBA AI Product Management","Linux Academy"],
}
ENABLES = [
("Linux","L3 Support"),("Linux","Docker"),("Linux","Kubernetes"),("Linux","Ansible"),
("AWS","AWS RDS"),("AWS","DynamoDB"),("AWS","Redshift"),("AWS","CloudFront"),
("AWS","AWS EMR"),("S3","AWS EMR"),("SQL","MySQL"),("SQL","PostgreSQL"),
("MySQL","Percona Server"),("Percona Server","Percona XtraDB Cluster"),
("Percona XtraDB Cluster","Galera"),("Docker","Kubernetes"),("Terraform","Infrastructure as Code"),
("Ansible","Infrastructure as Code"),("Git","CI/CD"),("WordPress","WooCommerce"),("WordPress","WP-CLI"),
("Magento","REST APIs"),("Python","AWS"),("Python","Automation"),("REST APIs","Webhooks"),
("L3 Support","Incident Response"),("Technical Account Management","Solutions Consulting"),
("Solutions Consulting","Solution Architecture"),("Product Management","Roadmap Planning"),
("UX/UI","Product Management")
]

def slug(s):
    return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')

def contains_term(text, term):
    pattern = r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, re.I) is not None

def count_term(text, term):
    pattern = r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"
    return len(re.findall(pattern, text, re.I))

def snippets(text, term, limit=2):
    out=[]
    for m in list(re.finditer(re.escape(term), text, re.I))[:limit]:
        out.append(text[max(0,m.start()-140):min(len(text),m.end()+180)])
    return out

def parse():
    ats = BeautifulSoup((SOURCES/"Blairs_Job_Titles_ATS.html").read_text(errors="ignore"), "html.parser")
    idx = BeautifulSoup((SOURCES/"index.html").read_text(errors="ignore"), "html.parser")
    ats_scripts="\n".join(s.get_text() for s in ats.find_all("script"))
    match=re.search(r'const jobData\s*=\s*(\[.*?\]);', ats_scripts, re.S)
    if not match:
        raise RuntimeError("jobData was not found")
    jobs=json.loads(match.group(1))
    idx_text=idx.get_text(" ",strip=True)

    skills=[]
    for domain, names in DOMAINS.items():
        for name in names:
            if contains_term(idx_text, name) or any(contains_term(str(j), name) for j in jobs):
                skills.append({"id":"skill:"+slug(name),"name":name,"domain":domain,
                               "source":"index.html","mention_count":count_term(idx_text,name)})
    skills={s["name"].lower():s for s in skills}
    skills=list(skills.values())

    roles=[]
    for n,j in enumerate(jobs,1):
        roles.append({"id":f"atsrole:{n}","title":j["title"],"family":j["category"],
                      "ats_potential":j["score"],"demand_signal":j["demand"],
                      "coverage_signal":j["coverage"],"match":j["match"],"gap":j["gap"],
                      "description":j["desc"],"source":"Blairs_Job_Titles_ATS.html"})

    portfolio=[]
    for h4 in idx.find_all("h4"):
        title=h4.get_text(" ",strip=True)
        if title and len(title)<140:
            context=h4.parent.get_text(" ",strip=True)[:2500] if h4.parent else ""
            portfolio.append({"id":"portfolio-role:"+slug(title),"title":title,
                              "source":"index.html","context":context})
    portfolio=list({p["id"]:p for p in portfolio}.values())

    role_edges=[]
    for r in roles:
        hay=" ".join([r["title"],r["family"],r["match"],r["description"]]).lower()
        for s in skills:
            if contains_term(hay, s["name"]):
                role_edges.append({"role_id":r["id"],"skill_id":s["id"],
                                   "evidence":"ATS title/category/match/description","weight":1.0})
    portfolio_edges=[]
    for p in portfolio:
        hay=(p["title"]+" "+p["context"]).lower()
        for s in skills:
            if contains_term(hay, s["name"]):
                portfolio_edges.append({"role_id":p["id"],"skill_id":s["id"],
                                        "evidence":"portfolio role title/context","weight":1.0})

    existing={s["name"] for s in skills}
    tree=[{"from":a,"to":b,"type":"ENABLES","basis":"design_inference"}
          for a,b in ENABLES if a in existing and b in existing]

    graph={"metadata":{"project":"Blair Skill Knowledge Graph","sources":["Blairs_Job_Titles_ATS.html","index.html"],
                       "ats_role_count":len(roles),"skill_count":len(skills),
                       "portfolio_role_count":len(portfolio),
                       "method":"Evidence-backed extraction with explicit inferred skill-tree edges"},
           "skills":skills,"ats_roles":roles,"portfolio_roles":portfolio,
           "role_skill_edges":role_edges,"portfolio_skill_edges":portfolio_edges,
           "skill_tree_edges":tree}
    OUT.write_text(json.dumps(graph,indent=2))
    print(json.dumps(graph["metadata"],indent=2))

if __name__=="__main__":
    parse()
