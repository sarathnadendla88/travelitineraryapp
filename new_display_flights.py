def display_flights(flights):
    st.header("✈️ Available Flights")

    if not flights or len(flights) == 0:
        st.warning("No flights available for this route.")
        return

    # Sort flights by price for better display
    try:
        sorted_flights = sorted(flights, key=lambda x: extract_price(x.get("price", 0)))
    except Exception as e:
        st.warning(f"Could not sort flights by price: {e}")
        sorted_flights = flights

    # Display flights in a grid
    for i, flight in enumerate(sorted_flights):
        with st.expander(f"{flight.get('airline', 'Airline')} - {flight.get('from', 'Origin')} to {flight.get('to', 'Destination')} - {flight.get('price', 'Price')}" + (" 🏆 Best Value!" if i == 0 else ""), expanded=True):
            # Flight details in a single column layout (no images)
            st.markdown(f"**Route:** {flight.get('from', 'Origin')} → {flight.get('to', 'Destination')}")

            # Flight number if available
            if 'flight_number' in flight:
                st.markdown(f"**Flight Number:** {flight.get('flight_number')}")

            # Departure and arrival information
            if 'departure_time' in flight or 'departure_date' in flight:
                dep_date = flight.get('departure_date', '')
                dep_time = flight.get('departure_time', '')
                if dep_date or dep_time:
                    st.markdown(f"**Departure:** {dep_date}{' at ' if dep_date and dep_time else ''}{dep_time}")

            if 'arrival_time' in flight or 'arrival_date' in flight:
                arr_date = flight.get('arrival_date', '')
                arr_time = flight.get('arrival_time', '')
                if arr_date or arr_time:
                    st.markdown(f"**Arrival:** {arr_date}{' at ' if arr_date and arr_time else ''}{arr_time}")
            
            # Layover information - moved here to display right after arrival information
            if 'layover_details' in flight and flight['layover_details']:
                layover_details = flight['layover_details']
                if not layover_details or len(layover_details) == 0:
                    st.markdown("**✅ Direct Flight**")
                else:
                    st.markdown(f"**🛑 Stops:** {len(layover_details)}")

                    # Display detailed layover information
                    st.markdown("**Layover Details:**")
                    for layover in layover_details:
                        city = layover.get('city', 'N/A')
                        duration = layover.get('duration', 'N/A')
                        arrival = layover.get('arrival_time', 'N/A')
                        departure = layover.get('departure_time', 'N/A')
                        terminal_change = layover.get('terminal_change', 'No')

                        # Create a formatted layover display
                        st.markdown(f"""<div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 5px;'>
                            <strong>🌆 {city}</strong> - ⏱️ {duration}<br>
                            🛬 Arrival: {arrival} | 🛫 Departure: {departure}<br>
                            {'🚶 Terminal change required' if terminal_change.lower() == 'yes' else '✓ No terminal change'}
                        </div>""", unsafe_allow_html=True)
            elif 'stops' in flight:
                stops = flight.get('stops', 0)
                if stops == 0:
                    st.markdown("**✅ Direct Flight**")
                else:
                    st.markdown(f"**🛑 Stops:** {stops}")
            elif 'layover' in flight and flight['layover']:
                if flight['layover'].lower() == 'direct flight' or flight['layover'] == '':
                    st.markdown("**✅ Direct Flight**")
                else:
                    st.markdown(f"**🛑 Layover:** {flight['layover']}")
            elif 'layovers' in flight and flight['layovers']:
                st.markdown(f"**🛑 Layover:** {flight['layovers']}")
            else:
                st.markdown("**✅ Direct Flight**")
                
            # Book now button for flight
            st.markdown(f"[Book Now]({flight.get('url', '#')})")
            
            # Add some space before fare class options
            st.markdown("")
            
            # Create a styled box for fare class information
            st.markdown("### Fare Class Options")

            # Get the current fare class
            current_fare_class = flight.get('class', 'Economy')

            # Get price and baggage information for the current fare class
            current_price = flight.get('price', 'N/A')

            # Set default baggage allowances based on airline standards if not provided
            current_fare_class_lower = current_fare_class.lower()

            # Default baggage allowances by class
            if 'economy' in current_fare_class_lower or 'standard' in current_fare_class_lower:
                default_check_in = '20 kg'
                default_hand = '7 kg'
            elif 'premium' in current_fare_class_lower:
                default_check_in = '25 kg'
                default_hand = '10 kg'
            elif 'business' in current_fare_class_lower or 'first' in current_fare_class_lower:
                default_check_in = '32 kg'
                default_hand = '14 kg'
            else:  # Default to economy if class is unknown
                default_check_in = '20 kg'
                default_hand = '7 kg'

            # Use provided values or defaults
            current_check_in = flight.get('check_in_baggage', default_check_in)
            current_hand = flight.get('hand_baggage', default_hand)

            # If values are empty or N/A, use defaults
            if current_check_in == 'N/A' or not current_check_in:
                current_check_in = default_check_in
            if current_hand == 'N/A' or not current_hand:
                current_hand = default_hand

            # Create a container with three columns for the three fare classes
            col_eco, col_premium, col_business = st.columns(3)

            # Economy Class
            with col_eco:
                # Determine if this is the current fare class
                is_current = 'economy' in current_fare_class.lower() or 'standard' in current_fare_class.lower()
                border_style = "border: 2px solid #4CAF50;" if is_current else ""

                # Display Economy class details
                st.markdown(f"""
                <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px; {border_style}">
                    <h4 style="margin-top: 0;">🔵 Economy</h4>
                    <p><strong>Price:</strong> {current_price if is_current else 'Available'}</p>
                    <p><strong>Check-in Baggage:</strong> {current_check_in if is_current else '15-20 kg (33-44 lbs)'}</p>
                    <p><strong>Hand Baggage:</strong> {current_hand if is_current else '7-8 kg (15-18 lbs)'}</p>
                </div>
                """, unsafe_allow_html=True)

            # Premium Economy Class
            with col_premium:
                # Determine if this is the current fare class
                is_current = 'premium' in current_fare_class.lower()
                border_style = "border: 2px solid #4CAF50;" if is_current else ""

                # Calculate premium economy price (typically 30-50% more than economy)
                if is_current:
                    premium_price = current_price
                    premium_check_in = current_check_in
                    premium_hand = current_hand
                else:
                    # If the current class is economy, estimate premium price
                    if 'economy' in current_fare_class.lower() or 'standard' in current_fare_class.lower():
                        try:
                            # Try to extract numeric value from price
                            price_value = ''.join(filter(lambda x: x.isdigit() or x == '.', str(current_price)))
                            if price_value:
                                base_price = float(price_value)
                                premium_price = f"~${int(base_price * 1.4)}" if '$' in str(current_price) else f"~{int(base_price * 1.4)}"
                            else:
                                premium_price = 'Available (30-50% more)'
                        except:
                            premium_price = 'Available (30-50% more)'
                        premium_check_in = '25-30 kg (55-66 lbs)'
                        premium_hand = '10-12 kg (22-26 lbs)'
                    else:  # If current class is business, estimate premium price
                        premium_price = 'Available (30-40% less than Business)'
                        premium_check_in = '25-30 kg (55-66 lbs)'
                        premium_hand = '10-12 kg (22-26 lbs)'

                # Display Premium Economy class details
                st.markdown(f"""
                <div style="background-color: #fff2e6; padding: 10px; border-radius: 5px; margin-bottom: 10px; {border_style}">
                    <h4 style="margin-top: 0;">⭐ Premium Economy</h4>
                    <p><strong>Price:</strong> {premium_price}</p>
                    <p><strong>Check-in Baggage:</strong> {premium_check_in}</p>
                    <p><strong>Hand Baggage:</strong> {premium_hand}</p>
                </div>
                """, unsafe_allow_html=True)

            # Business Class
            with col_business:
                # Determine if this is the current fare class
                is_current = 'business' in current_fare_class.lower() or 'first' in current_fare_class.lower()
                border_style = "border: 2px solid #4CAF50;" if is_current else ""

                # Calculate business price (typically 2-3x more than economy)
                if is_current:
                    business_price = current_price
                    business_check_in = current_check_in
                    business_hand = current_hand
                else:
                    # If the current class is economy, estimate business price
                    if 'economy' in current_fare_class.lower() or 'standard' in current_fare_class.lower():
                        try:
                            # Try to extract numeric value from price
                            price_value = ''.join(filter(lambda x: x.isdigit() or x == '.', str(current_price)))
                            if price_value:
                                base_price = float(price_value)
                                business_price = f"~${int(base_price * 2.5)}" if '$' in str(current_price) else f"~{int(base_price * 2.5)}"
                            else:
                                business_price = 'Available (2-3x more)'
                        except:
                            business_price = 'Available (2-3x more)'
                        business_check_in = '30-40 kg (66-88 lbs)'
                        business_hand = '14-18 kg (31-40 lbs)'
                    else:  # If current class is premium, estimate business price
                        try:
                            # Try to extract numeric value from price
                            price_value = ''.join(filter(lambda x: x.isdigit() or x == '.', str(current_price)))
                            if price_value:
                                base_price = float(price_value)
                                business_price = f"~${int(base_price * 1.8)}" if '$' in str(current_price) else f"~{int(base_price * 1.8)}"
                            else:
                                business_price = 'Available (70-100% more)'
                        except:
                            business_price = 'Available (70-100% more)'
                        business_check_in = '30-40 kg (66-88 lbs)'
                        business_hand = '14-18 kg (31-40 lbs)'

                # Display Business class details
                st.markdown(f"""
                <div style="background-color: #e6f7ff; padding: 10px; border-radius: 5px; margin-bottom: 10px; {border_style}">
                    <h4 style="margin-top: 0;">✨ Business</h4>
                    <p><strong>Price:</strong> {business_price}</p>
                    <p><strong>Check-in Baggage:</strong> {business_check_in}</p>
                    <p><strong>Hand Baggage:</strong> {business_hand}</p>
                </div>
                """, unsafe_allow_html=True)
