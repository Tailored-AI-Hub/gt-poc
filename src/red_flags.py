from collections import defaultdict
from fuzzywuzzy import fuzz

from src.analyzer import are_layouts_similar


def group_similar_vendors(vendor_names, threshold=90):
    """
    Group vendor names that are similar based on fuzzy matching.
    Returns a dict: canonical_vendor_name -> set of similar vendor names
    """
    groups = []
    for v in vendor_names:
        found = False
        for group in groups:
            if any(fuzz.token_set_ratio(v, g) >= threshold for g in group):
                group.add(v)
                found = True
                break
        if not found:
            groups.append(set([v]))
    # Map each vendor to its canonical (first) name in the group
    vendor_to_canonical = {}
    for group in groups:
        canonical = sorted(group)[0]
        for v in group:
            vendor_to_canonical[v] = canonical
    return vendor_to_canonical


def find_similar_format_groups(invoices, vendor_to_canonical):
    """
    Find groups of documents that have similar formats but different vendors.
    Returns a list of document groups.
    """
    format_groups = []
    processed = set()
    
    for i, inv1 in enumerate(invoices):
        if i in processed:
            continue
            
        vendor1 = (inv1.get("vendor_name") or "").strip()
        canonical_vendor1 = vendor_to_canonical.get(vendor1, vendor1)
        headers1 = inv1.get("table_headers", [])
        table_size1 = inv1.get("table_size", None)
        scanned_or_typed1 = (inv1.get("scanned_or_typed") or "")
        handwritten_or_typed1 = (inv1.get("handwritten_or_typed") or "")
        
        current_group = [inv1]
        processed.add(i)
        
        for j, inv2 in enumerate(invoices):
            if j in processed or j == i:
                continue
                
            vendor2 = (inv2.get("vendor_name") or "").strip()
            canonical_vendor2 = vendor_to_canonical.get(vendor2, vendor2)
            
            # Only compare if different vendors
            if canonical_vendor1 != canonical_vendor2:
                headers2 = inv2.get("table_headers", [])
                table_size2 = inv2.get("table_size", None)
                scanned_or_typed2 = (inv2.get("scanned_or_typed") or "")
                handwritten_or_typed2 = (inv2.get("handwritten_or_typed") or "")
                
                is_similar, sim = are_layouts_similar(
                    headers1, headers2,
                    scanned_or_typed1, scanned_or_typed2,
                    table_size1, table_size2,
                    handwritten_or_typed1, handwritten_or_typed2
                )
                
                if sim > 0.9 and scanned_or_typed1 == scanned_or_typed2 and (handwritten_or_typed1 == handwritten_or_typed2):
                    current_group.append(inv2)
                    processed.add(j)
        
        if len(current_group) > 1:  # Only add groups with multiple documents
            format_groups.append(current_group)
    
    return format_groups


def detect_red_flags(invoices):
    """
    invoices: list of dicts with fields:
        - file_name
        - vendor_name
        - phone_numbers
        - email_addresses
        - table_headers
        - format_style
    Returns:
        list of invoice dicts with 'flag_type' and 'flag_reason'
    """
    contact_map = defaultdict(list)
    vendor_map = defaultdict(list)
    flagged = []

    # Group similar vendor names
    all_vendor_names = [(inv.get("vendor_name") or "").strip() for inv in invoices]
    vendor_to_canonical = group_similar_vendors(all_vendor_names)

    # Build lookup maps
    for inv in invoices:
        phones = inv.get("phone_numbers", [])
        emails = inv.get("email_addresses", [])
        vendor = (inv.get("vendor_name") or "").strip()
        canonical_vendor = vendor_to_canonical.get(vendor, vendor)

        for p in phones:
            contact_map[p].append(canonical_vendor)
        for e in emails:
            contact_map[e].append(canonical_vendor)

        vendor_map[canonical_vendor].append(inv)

    # Find similar format groups
    similar_format_groups = find_similar_format_groups(invoices, vendor_to_canonical)
    
    # Create a mapping of documents to their format group
    doc_to_format_group = {}
    for group_idx, group in enumerate(similar_format_groups):
        for doc in group:
            doc_to_format_group[doc['file_name']] = group_idx

    for inv in invoices:
        flag_type = "✅ Green Flag"
        flag_reason = "No issues detected."

        vendor = (inv.get("vendor_name") or "").strip()
        canonical_vendor = vendor_to_canonical.get(vendor, vendor)
        phones = inv.get("phone_numbers", [])
        emails = inv.get("email_addresses", [])
        headers = inv.get("table_headers", [])
        table_size = inv.get("table_size", None)
        scanned_or_typed = (inv.get("scanned_or_typed") or "")
        handwritten_or_typed = (inv.get("handwritten_or_typed") or "")

        # 🚩 Same contact, different vendors (using canonical vendor)
        for contact in phones + emails:
            vendors = set(contact_map.get(contact, []))
            if len(vendors) > 1 and (len(vendors - {canonical_vendor}) > 0):
                flag_type = "🚩 Shared Contact Info"
                flag_reason = f"Contact {contact} used by multiple vendors: {vendors}"
                break

        # 🚩 Same format, different vendors
        if flag_type == "✅ Green Flag":
            if inv['file_name'] in doc_to_format_group:
                group_idx = doc_to_format_group[inv['file_name']]
                group = similar_format_groups[group_idx]
                other_vendors = [doc['vendor_name'] for doc in group if doc['file_name'] != inv['file_name']]
                flag_type = "🚩 Same Format, Different Vendor"
                flag_reason = f"Part of format group with vendors: {', '.join(other_vendors)} (group_id={group_idx})"

        # 🚩 Different format, same vendor (using canonical vendor)
        if flag_type == "✅ Green Flag":
            my_invoices = vendor_map.get(canonical_vendor, [])
            for other in my_invoices:
                if other == inv:
                    continue
                is_similar, sim = are_layouts_similar(
                    headers, other.get("table_headers", []),
                    scanned_or_typed, other.get("scanned_or_typed"),
                    table_size, other.get("table_size"),
                    handwritten_or_typed, other.get("handwritten_or_typed")
                )
                if sim < 0.4 or scanned_or_typed != other.get("scanned_or_typed") or (handwritten_or_typed != (other.get("handwritten_or_typed") or "")):
                    flag_type = "🚩 Different Format, Same Vendor"
                    flag_reason = f"Other invoice for {vendor} has different format/layout (similarity={sim:.2f})"
                    break

        inv["flag_type"] = flag_type
        inv["flag_reason"] = flag_reason
        inv["canonical_vendor"] = canonical_vendor
        inv["format_group_id"] = doc_to_format_group.get(inv['file_name'], None)
        flagged.append(inv)

    return flagged