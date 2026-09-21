# -*- coding: utf-8 -*-
"""
Created on Mon Sep 21 12:42:50 2026

@author: Chris Cortez
"""

import datetime
from database import Resource, SessionLocal, engine
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit as st

st.set_page_config(page_title="CRIS - Resource Intelligence", layout="wide")
geolocator = Nominatim(user_agent="cris_prototype_app")

st.title("🛡️ CRIS: Community Resource Intelligence System")
st.subheader("OSINT-Driven Resource Mapping & Search Party CTF")

# Sidebar: Dynamic Gamification Leaderboard
st.sidebar.header("🏆 Search Party Leaderboard")

db_sidebar = SessionLocal()
verified_items = db_sidebar.query(Resource).filter(Resource.verification_status == "Verified").all()
db_sidebar.close()

if verified_items:
    student_stats = {}
    for item in verified_items:
        student = item.verified_by_student or "Unknown"
        if student not in student_stats:
            student_stats[student] = {"count": 0, "points": 0}
        student_stats[student]["count"] += 1
        student_stats[student]["points"] += (item.points_awarded if item.points_awarded else 10)

    sorted_students = sorted(student_stats.items(), key=lambda x: x[1]["points"], reverse=True)

    st.sidebar.markdown("**Top Student Analysts (This Week):**")
    for idx, (student_name, stats) in enumerate(sorted_students[:5], start=1):
        st.sidebar.markdown(f"{idx}. `{student_name}` - {stats['points']} pts ({stats['count']} verified)")
else:
    st.sidebar.info("No verified intelligence yet. Leaderboard will populate as submissions are approved!")

tab1, tab2, tab3 = st.tabs(
    [
        "🗺️ Live Verified Resource Map",
        "🚩 Submit New Resource (Capture Flag)",
        "🔍 Verification Queue",
    ]
)

# -------------------------------------------------------------------
# TAB 1: LIVE MAP & FINDHELP-STYLE FILTER GUI (WITH DISTANCE & GRANULAR LOCATION)
# -------------------------------------------------------------------
with tab1:
    st.header("Community Resource Directory & Map")
    st.markdown("Search, filter by location components, and analyze service reach.")

    # Filter Controls UI
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        search_term = st.text_input("🔍 Search Org", placeholder="e.g., Food Bank...")
        category_filter = st.selectbox(
            "📂 Category",
            ["All Categories", "Rental Assistance", "Emergency Shelter", "Food Pantry", "Utility Assistance", "Legal Aid"]
        )
    with filter_col2:
        city_filter = st.text_input("🏙️ City", placeholder="e.g., San Antonio")
        state_filter = st.text_input("📍 State", placeholder="e.g., TX")
    with filter_col3:
        zip_filter = st.text_input("📮 Zip Code", placeholder="e.g., 78205")
        county_filter = st.text_input("🏛️ County", placeholder="e.g., Bexar")

    # Distance Bar Slider (Up to 100 Miles)
    st.markdown("---")
    max_distance = st.slider("🚗 Maximum Search Radius (Miles from Center)", min_value=5, max_value=100, value=50, step=5)

    db = SessionLocal()
    query = db.query(Resource).filter(Resource.verification_status == "Verified")

    # Apply database string filters
    if search_term:
        query = query.filter(Resource.org_name.ilike(f"%{search_term}%"))
    if city_filter:
        query = query.filter(Resource.city.ilike(f"%{city_filter}%"))
    if state_filter:
        query = query.filter(Resource.state.ilike(f"%{state_filter}%"))
    if zip_filter:
        query = query.filter(Resource.zip_code.ilike(f"%{zip_filter}%"))
    if county_filter:
        query = query.filter(Resource.county.ilike(f"%{county_filter}%"))
    if category_filter != "All Categories":
        query = query.filter(Resource.category == category_filter)

    resources = query.all()

    # Center reference point for distance calculation (San Antonio downtown default)
    center_coords = (29.4241, -98.4936)
    
    # Filter by distance radius (up to 100 miles)
    filtered_resources = []
    for r in resources:
        if r.latitude and r.longitude:
            dist = geodesic(center_coords, (r.latitude, r.longitude)).miles
            if dist <= max_distance:
                filtered_resources.append(r)

    if filtered_resources:
        df = pd.DataFrame([r.__dict__ for r in filtered_resources])

        # Render Folium Map
        m = folium.Map(location=center_coords, zoom_start=10)
        for _, row in df.iterrows():
            color = "green" if "Open" in str(row["funding_status"]) else "red"
            full_addr = f"{row.get('street_address', '')}, {row.get('city', '')}, {row.get('state', '')} {row.get('zip_code', '')}"
            
            popup_content = f"<b>{row['org_name']}</b><br>Category: {row['category']}<br>Status: {row['funding_status']}<br>Address: {full_addr}"
            if row.get("proof_url"):
                popup_content += f"<br><a href='{row['proof_url']}' target='_blank'>🔗 Open Source Link / Proof</a>"

            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"{row['org_name']} ({row['category']})",
                icon=folium.Icon(color=color, icon="info-sign"),
            ).add_to(m)

        st_folium(m, width=1100, height=450)
        
        st.subheader(f"Matching Resources Within {max_distance} Miles ({len(filtered_resources)} found)")
        st.dataframe(
            df[["org_name", "category", "funding_status", "street_address", "city", "state", "zip_code", "county", "eligibility_notes"]],
            use_container_width=True
        )
    else:
        st.info("No verified resources match your criteria within the selected distance radius.")
    
    db.close()

# -------------------------------------------------------------------
# TAB 2: CTF SUBMISSION PORTAL (GRANULAR LOCATION INPUTS)
# -------------------------------------------------------------------
with tab2:
    st.header("Log New Intelligence (Submit a Resource Flag)")
    with st.form("resource_form"):
        student_id = st.text_input("Student / Analyst ID", value="Student_MSW")
        org_name = st.text_input("Organization / Program Name")
        category = st.selectbox(
            "Category",
            ["Rental Assistance", "Emergency Shelter", "Food Pantry", "Utility Assistance", "Legal Aid"]
        )
        
        st.markdown("**Location Breakdown:**")
        street_address = st.text_input("Street Address", placeholder="e.g., 123 Main St")
        
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        with col_c1:
            city = st.text_input("City", placeholder="San Antonio")
        with col_c2:
            state = st.text_input("State", placeholder="TX")
        with col_c3:
            zip_code = st.text_input("Zip Code", placeholder="78205")
        with col_c4:
            county = st.text_input("County", placeholder="Bexar")

        funding_status = st.selectbox(
            "Funding / Intake Status",
            ["Open & Active Funds", "Waitlist Only", "Exhausted / Closed Intake"]
        )
        eligibility_notes = st.text_area("Eligibility Requirements (Income, IDs, Zip Codes)")
        proof_url = st.text_input("Source URL / OSINT Proof Link")

        submitted = st.form_submit_button("Submit Flag for Verification")

        if submitted:
            # Construct full string for geocoding
            full_address_string = f"{street_address}, {city}, {state} {zip_code}"
            try:
                location = geolocator.geocode(full_address_string)
                lat, lon = (location.latitude, location.longitude) if location else (29.4241, -98.4936)
            except:
                lat, lon = 29.4241, -98.4936

            db = SessionLocal()
            new_resource = Resource(
                org_name=org_name,
                category=category,
                street_address=street_address,
                city=city,
                state=state,
                zip_code=zip_code,
                county=county,
                latitude=lat,
                longitude=lon,
                funding_status=funding_status,
                eligibility_notes=eligibility_notes,
                proof_url=proof_url,
                verified_by_student=student_id,
                verification_status="Pending",
            )
            db.add(new_resource)
            db.commit()
            db.close()
            st.success(f"Flag logged successfully! Submitted to Verification Queue. +10 Pending Points for {student_id}.")

# -------------------------------------------------------------------
# TAB 3: VERIFICATION QUEUE
# -------------------------------------------------------------------
with tab3:
    st.header("Pending Intelligence Review")
    db = SessionLocal()
    pending = db.query(Resource).filter(Resource.verification_status == "Pending").all()

    if not pending:
        st.info("No pending submissions in the queue.")

    for item in pending:
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{item.org_name}** ({item.category}) — Submitted by `{item.verified_by_student}`")
                full_addr = f"{item.street_address}, {item.city}, {item.state} {item.zip_code} ({item.county} County)"
                st.write(f"Address: {full_addr} | Status: {item.funding_status}")
                st.write(f"Notes: {item.eligibility_notes}")
                if item.proof_url:
                    st.write(f"Proof: [Link]({item.proof_url})")
            with col2:
                if st.button("Approve & Publish", key=f"app_{item.id}"):
                    item.verification_status = "Verified"
                    item.last_verified = datetime.datetime.utcnow()
                    db.commit()
                    st.success(f"Approved {item.org_name}!")
                    st.rerun()

            with st.expander(f"❌ Reject Submission: {item.org_name}", expanded=False):
                reject_reason_input = st.text_area(
                    "Reason for Rejection:", 
                    key=f"reason_text_{item.id}", 
                    placeholder="e.g., Outdated funding info, incorrect address..."
                )
                
                if st.button("Confirm Rejection", key=f"rej_confirm_{item.id}", type="primary"):
                    if reject_reason_input.strip():
                        item.verification_status = "Rejected"
                        item.rejection_reason = reject_reason_input
                        db.commit()
                        st.warning("Submission rejected and logged.")
                        st.rerun()
                    else:
                        st.error("Please provide a reason for rejection before confirming.")

    db.close()