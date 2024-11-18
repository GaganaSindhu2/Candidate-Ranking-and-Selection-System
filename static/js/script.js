
// Update range options based on selected criterion
function updateRangeOptions() {
    var criterion = document.getElementById('criterion').value;
    var rangeDropdown = document.getElementById('range');

    // Clear existing options
    rangeDropdown.innerHTML = '';

    // Add appropriate ranges based on the selected criterion
    if (criterion === 'CGPA') {
        rangeDropdown.innerHTML = `
            <option value="7-10">7-10</option>
            <option value="8-10">8-10</option>
            <option value="9-10">9-10</option>
            <option value="All">All</option>
        `;
    } else if (criterion === 'Interview Test Score') {
        rangeDropdown.innerHTML = `
            <option value="70-100">70-100</option>
            <option value="80-100">80-100</option>
            <option value="90-100">90-100</option>
            <option value="All">All</option>
        `;
    }
}

// Classify candidates based on selected criterion and range
function classifyCandidates() {
    var criterion = document.getElementById('criterion').value;
    var range = document.getElementById('range').value;

    fetch('/classify_candidates', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `criterion=${criterion}&range=${range}`
    })
    .then(response => response.json())
    .then(data => {
        var tableBody = document.getElementById('results-table').getElementsByTagName('tbody')[0];
        tableBody.innerHTML = '';  // Clear previous results

        // Populate table with the results
        data.forEach(function(row) {
            var newRow = tableBody.insertRow();
            newRow.insertCell().textContent = row[0]; // Candidate ID
            newRow.insertCell().textContent = row[1]; // Name
            newRow.insertCell().textContent = row[2]; // Phone
            newRow.insertCell().textContent = row[3]; // Email
            newRow.insertCell().textContent = row[4]; // CGPA or Interview Test Score
        });
    })
    .catch(err => console.log('Error:', err));
}
//update candidate
function showFieldInput() {
    const selectedField = document.getElementById("field-select").value;
    const fields = ["name", "email", "phone", "cgpa", "interview_score"];
    
    // Hide all input fields initially
    fields.forEach(field => {
        document.getElementById(field + "-input").style.display = "none";
    });
    
    // Show only the selected field
    if (selectedField) {
        document.getElementById(selectedField + "-input").style.display = "block";
    }
}