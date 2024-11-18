from flask import Flask, render_template, request, redirect, flash, jsonify, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'some_secret_key'  # Required for flashing messages and sessions

# MySQL Database connection
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="Sindhu2908",  # Replace with your MySQL password
        database="project"
    )

@app.route('/')
def home():
    return redirect('/login')  # Redirect to login page by default

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Connect to the database
        conn = connect_db()
        cursor = conn.cursor()

        # Query to check if the user exists with the provided username and password
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            # If the user is found, login is successful
            session['username'] = username  # Store the username in session
            flash("Login successful!", "success")
            return redirect('/add_candidate')  # Redirect to add_candidate page after successful login
        else:
            flash("Invalid username or password, please try again.", "error")
        
        cursor.close()
        conn.close()

    return render_template('login.html')
@app.route('/classify_candidates')
def classify_page():
    return render_template('classify_candidates.html')

# Route to display the update candidate page
@app.route('/update_candidate')
def update_candidate_page():
    return render_template('update_candidate.html')

# Route to display the delete candidate page
@app.route('/delete_candidate')
def delete_candidate_page():
    return render_template('delete_candidate.html')

@app.route('/add_candidate', methods=['GET', 'POST'])
@app.route('/add_candidate', methods=['GET', 'POST'])
def add_candidate_page():
    if 'username' not in session:  # Check if the user is logged in
        flash("Please log in first.", "error")
        return redirect('/login')
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        cgpa = request.form['cgpa']
        interview_score = request.form['interview_score']
        title = request.form['title']

        # Validate CGPA
        try:
            cgpa = float(cgpa)
            if not (0 <= cgpa <= 10):
                flash("CGPA must be between 0 and 10.", 'error')
                return redirect('/add_candidate')
        except ValueError:
            flash("Invalid CGPA format.", 'error')
            return redirect('/add_candidate')

        # Validate Interview Score
        try:
            interview_score = float(interview_score)
            if not (0 <= interview_score <= 100):
                flash("Interview score must be between 0 and 100.", 'error')
                return redirect('/add_candidate')
        except ValueError:
            flash("Invalid interview score format.", 'error')
            return redirect('/add_candidate')

        # Calculate description based on interview score
        description = "Eligible" if interview_score > 50 else "Not Eligible"

        conn = connect_db()
        cursor = conn.cursor()

        # Calculate total score using the MySQL function
        cursor.execute("SELECT calculate_total_score(%s, %s)", (cgpa, interview_score))
        total_score = cursor.fetchone()[0]

        # Determine criteria name and weight
        if cgpa >= (interview_score / 100) * 10:  # Compare normalized values
            criteria_name = "CGPA"
            weight = (cgpa / 10) * 100
        else:
            criteria_name = "Interview Test Score"
            weight = interview_score

        # Insert into candidate table
        candidate_query = """
            INSERT INTO candidate (name, email, phone_no, cgpa, interview_test_score, total_score)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        candidate_values = (name, email, phone, cgpa, interview_score, total_score)

        try:
            cursor.execute(candidate_query, candidate_values)
            candidate_id = cursor.lastrowid  # Retrieve the last inserted candidate_id

            # Insert into position table
            position_query = "INSERT INTO positions (title, description, candidate_id) VALUES (%s, %s, %s)"
            cursor.execute(position_query, (title, description, candidate_id))
            position_id = cursor.lastrowid  # Retrieve the last inserted position_id

            # Insert into application table
            application_query = "INSERT INTO application (candidate_id, position_id) VALUES (%s, %s)"
            cursor.execute(application_query, (candidate_id, position_id))
            application_id = cursor.lastrowid  # Retrieve the last inserted application_id

            # Insert into ranking table with calculated rank
            ranking_query = """
                INSERT INTO ranking (application_id, total_score, `rank`)
                SELECT %s, %s, (SELECT COUNT(*) + 1 FROM candidate WHERE cgpa > %s)
            """
            cursor.execute(ranking_query, (application_id, total_score, cgpa))

            # Insert into selection_criteria table
            selection_query = """
                INSERT INTO selection_criteria (position_id, criteria_name, weight)
                VALUES (%s, %s, %s)
            """
            cursor.execute(selection_query, (position_id, criteria_name, weight))

            conn.commit()
            flash("Candidate added successfully!")
        except mysql.connector.Error as err:
            flash(f"Database Error: {err}", 'error')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

        return redirect('/add_candidate')
    
    return render_template('add_candidate.html')


# Update a candidate's details
@app.route('/update_candidate', methods=['POST'])
def update_candidate():
    candidate_id = request.form['candidate_id']
    field = request.form['field']
    new_value = request.form.get(field)  # Get the value of the selected field

    if not candidate_id or not field or not new_value:
        flash("All fields are required!", 'error')
        return redirect('/update_candidate')

    conn = connect_db()
    cursor = conn.cursor()

    # Update query based on the selected field
    query = f"UPDATE candidate SET {field} = %s WHERE candidate_id = %s"
    values = (new_value, candidate_id)

    try:
        cursor.execute(query, values)
        conn.commit()
        flash("Candidate updated successfully!", 'success')
    except mysql.connector.Error as err:
        flash(f"Database Error: {err}", 'error')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return redirect('/update_candidate')

@app.route('/classify_candidates', methods=['POST'])
@app.route('/classify_candidates', methods=['POST'])
def classify_candidates():
    criterion = request.form['criterion']
    selected_range = request.form['range']

    conn = connect_db()
    cursor = conn.cursor()

    # Classify by CGPA
    if criterion == "CGPA":
        if selected_range == "All":
            query = "SELECT candidate_id, name, phone_no, email, cgpa, total_score FROM candidate ORDER BY cgpa DESC"
        else:
            lower_bound, upper_bound = map(float, selected_range.split('-'))
            query = "SELECT candidate_id, name, phone_no, email, cgpa, total_score FROM candidate WHERE cgpa >= %s AND cgpa <= %s ORDER BY cgpa DESC"
            cursor.execute(query, (lower_bound, upper_bound))
            rows = cursor.fetchall()

    # Classify by Interview Test Score
    elif criterion == "Interview Test Score":
        if selected_range == "All":
            query = "SELECT candidate_id, name, phone_no, email, interview_test_score, total_score FROM candidate ORDER BY interview_test_score DESC"
        else:
            lower_bound, upper_bound = map(float, selected_range.split('-'))
            query = "SELECT candidate_id, name, phone_no, email, interview_test_score, total_score FROM candidate WHERE interview_test_score >= %s AND interview_test_score <= %s ORDER BY interview_test_score DESC"
            cursor.execute(query, (lower_bound, upper_bound))
            rows = cursor.fetchall()

    else:
        # If neither criterion is matched, set rows to empty to prevent errors
        rows = []

    # Fetch all rows if no specific range was given
    if selected_range == "All":
        cursor.execute(query)
        rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(rows)  # Return the query result in JSON format

# Delete a candidate
@app.route('/delete_candidate', methods=['POST'])
def delete_candidate():
    candidate_id = request.form['candidate_id']

    conn = connect_db()
    cursor = conn.cursor()

    query = "DELETE FROM candidate WHERE candidate_id = %s"
    cursor.execute(query, (candidate_id,))
    conn.commit()

    cursor.close()
    conn.close()

    flash("Candidate deleted successfully!", 'success')
    return redirect('/delete_candidate')



if __name__ == '__main__':
    app.run(debug=True)