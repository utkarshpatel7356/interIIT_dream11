// Add JavaScript functionality here if needed
// Form validation for team selection

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    
    if (form) {
        form.addEventListener('submit', function(event) {
            const team1 = document.querySelector('select[name="team1"]').value;
            const team2 = document.querySelector('select[name="team2"]').value;
            const venue = document.querySelector('select[name="venue"]').value;
            
            // Validate selections
            if (!team1 || team1 === 'Select Team 1') {
                alert('Please select Team 1');
                event.preventDefault();
                return;
            }
            
            if (!team2 || team2 === 'Select Team 2') {
                alert('Please select Team 2');
                event.preventDefault();
                return;
            }
            
            if (!venue || venue === 'Select Venue') {
                alert('Please select a Venue');
                event.preventDefault();
                return;
            }
            
            if (team1 === team2) {
                alert('Please select different teams');
                event.preventDefault();
                return;
            }
            
            // If all validations pass, allow form submission
        });
    }
});
