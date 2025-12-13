import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from scholarly import scholarly
import json

# List of Google Scholar profiles to parse
profiles = [
    "pIK4eZ0AAAAJ",
    "GVsyMf8AAAAJ",
    "IkRvFZkAAAAJ"
]

def clean_text(text):
    """Clean text by removing HTML tags and extra whitespace"""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', str(text))
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_authors(authors_str):
    """Parse authors string and format it in lastname, first initial format"""
    if not authors_str or authors_str == "Unknown Authors":
        return "Unknown Authors"
    
    def format_single_author(name):
        """Format a single author name to 'Lastname, F.' format"""
        name = name.strip()
        if not name:
            return ""
        
        # Handle names that are already in "Lastname, F." format
        if ',' in name and len(name.split(',')) == 2:
            parts = name.split(',')
            lastname = parts[0].strip()
            firstname = parts[1].strip()
            if len(firstname) <= 2:  # Already an initial
                return f"{lastname}, {firstname}"
            else:
                return f"{lastname}, {firstname[0]}."
        
        # Split by whitespace
        parts = name.split()
        if len(parts) == 1:
            return parts[0]  # Only one name, assume it's lastname
        
        # Assume last part is lastname, everything else is firstname(s)
        lastname = parts[-1]
        firstname_parts = parts[:-1]
        
        # Take first letter of each firstname part
        initials = ''.join([part[0].upper() + '.' for part in firstname_parts if part])
        
        return f"{lastname}, {initials}"
    
    # Split by common separators
    authors = re.split(r'[,;]|and\s+', authors_str)
    authors = [author.strip() for author in authors if author.strip()]
    
    # Format each author
    formatted_authors = []
    for author in authors:
        formatted = format_single_author(author)
        if formatted:
            formatted_authors.append(formatted)
    
    # Return with proper APA formatting (& before last author)
    if len(formatted_authors) > 3:
        return f"{formatted_authors[0]}, {formatted_authors[1]}, {formatted_authors[2]} et al."
    elif len(formatted_authors) == 1:
        return formatted_authors[0]
    elif len(formatted_authors) == 2:
        return f"{formatted_authors[0]} & {formatted_authors[1]}"
    elif len(formatted_authors) == 3:
        return f"{formatted_authors[0]}, {formatted_authors[1]} & {formatted_authors[2]}"
    else:
        return "Unknown Authors"

# Function to fetch publications from a Google Scholar profile
def fetch_publications(profile_id):
    try:
        print(f"Fetching publications for profile: {profile_id}")
        author = scholarly.search_author_id(profile_id)
        author = scholarly.fill(author, sections=["publications"])
        
        print(f"Found {len(author['publications'])} publications")

        publications = []
        for i, pub in enumerate(author["publications"]):
            # Fill publication details to get more information
            filled_pub = pub  # Default to original pub
            try:
                filled_pub = scholarly.fill(pub)
                bib = filled_pub.get("bib", {})
            except:
                bib = pub.get("bib", {})
            
            # Debug: print available fields for first few publications
            if i < 3:
                print(f"Publication {i+1} bib fields:", list(bib.keys()))
                print(f"Sample bib data:", json.dumps(bib, indent=2, default=str)[:500])
            
            # Extract fields with multiple possible names
            title = clean_text(bib.get("title", "Unknown Title"))
            year = bib.get("pub_year") or bib.get("year", "Unknown Year")
            
            # Try different field names for authors
            authors = (bib.get("author") or 
                      bib.get("authors") or 
                      "Unknown Authors")
            authors = parse_authors(clean_text(authors))
            
            # Try different field names for venue/journal
            venue = (bib.get("venue") or 
                    bib.get("journal") or 
                    bib.get("booktitle") or 
                    bib.get("conference") or 
                    bib.get("publisher") or
                    "Unknown Journal")
            venue = clean_text(venue)
            
            volume = clean_text(bib.get("volume", ""))
            issue = clean_text(bib.get("number", ""))
            pages = clean_text(bib.get("pages", ""))
            
            # Try to extract DOI from various fields
            doi = bib.get("doi") or bib.get("DOI", "")
            if not doi and "eprint_url" in filled_pub:
                eprint_url = filled_pub["eprint_url"]
                if "doi.org" in eprint_url:
                    doi = eprint_url.split("doi.org/")[-1]
            
            link = filled_pub.get("eprint_url") or filled_pub.get("pub_url", "")

            publications.append({
                "title": title,
                "year": str(year),
                "authors": authors,
                "venue": venue,
                "volume": volume,
                "issue": issue,
                "pages": pages,
                "doi": doi,
                "link": link
            })

        return publications
    
    except Exception as e:
        print(f"Error fetching publications for {profile_id}: {e}")
        return []

# Aggregate all publications and remove duplicates
all_publications = []
for profile in profiles:
    publications = fetch_publications(profile)
    all_publications.extend(publications)

print(f"Total publications fetched: {len(all_publications)}")

# Remove duplicates based on title (case-insensitive)
seen_titles = set()
unique_publications = []
for pub in all_publications:
    title_lower = pub['title'].lower()
    if title_lower not in seen_titles:
        seen_titles.add(title_lower)
        unique_publications.append(pub)

print(f"Unique publications after deduplication: {len(unique_publications)}")

# Filter publications to keep only 2019 and later
filtered_publications = []
for pub in unique_publications:
    year = pub['year']
    try:
        year_int = int(year)
        if year_int >= 2019:
            filtered_publications.append(pub)
    except (ValueError, TypeError):
        # Skip publications without valid year data
        continue

print(f"Publications after filtering (2019 and later): {len(filtered_publications)}")

# Sort publications by year (descending), then by title
try:
    sorted_publications = sorted(filtered_publications, 
                               key=lambda x: (int(x['year']) if x['year'].isdigit() else 0, x['title']), 
                               reverse=True)
except:
    sorted_publications = sorted(filtered_publications, key=lambda x: x['title'])

# Generate QMD content
qmd_content = """---
title: "Publications"
---

This page was auto-generated using data from Google Scholar.

"""

current_year = None
for pub in sorted_publications:
    year = pub['year']
    title = pub['title']
    authors = pub['authors']
    venue = pub['venue']
    volume = pub['volume']
    issue = pub['issue']
    pages = pub['pages']
    doi = pub['doi']
    link = pub['link']

    # Skip if no meaningful data
    if title == "Unknown Title" and venue == "Unknown Journal":
        continue

    if year != current_year:
        if current_year is not None:
            qmd_content += "\n"
        qmd_content += f"### {year}\n\n"
        current_year = year

    # Format the citation in APA style like Poldrack Lab
    qmd_content += f"{authors} ({year}). {title}."
    
    if venue and venue != "Unknown Journal":
        qmd_content += f" *{venue}*"
        if volume:
            qmd_content += f", **{volume}**"
            if issue:
                qmd_content += f"({issue})"
        if pages:
            qmd_content += f", {pages}"
    
    qmd_content += "."
    
    # Add links
    links = []
    if doi:
        links.append(f"[DOI](https://doi.org/{doi})")
    if link and "doi.org" not in link:
        links.append(f"[OA]({link})")
    
    if links:
        qmd_content += " " + " ".join(links)
    
    qmd_content += "\n\n"

# Write to a QMD file only if we have publications
output_path = "/home/pedro/Repos/xcit_website_2025/publications.qmd"
if len(sorted_publications) > 0:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(qmd_content)
    print(f"QMD file generated successfully at: {output_path}")
    print("Sample of generated content:")
    print(qmd_content[:500] + "..." if len(qmd_content) > 500 else qmd_content)
else:
    print("ERROR: No publications fetched. The output file was NOT overwritten.")
    print("This may be due to Google Scholar rate limiting. Try again later.")
