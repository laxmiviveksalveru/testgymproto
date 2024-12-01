function calculateFat() {
    const gender = document.getElementById('gender').value;
    const age = document.getElementById('age').value;
    const height = parseFloat(document.getElementById('height').value);
    const neck = parseFloat(document.getElementById('neck').value);
    const waist = parseFloat(document.getElementById('waist').value);
    const hip = parseFloat(document.getElementById('hip').value);
  
    if (!height || !neck || !waist || (gender === 'female' && !hip)) {
      alert("Please fill in all required fields.");
      return;
    }
  
    let bodyFatPercentage;
  
    if (gender === 'male') {
      bodyFatPercentage = 495 / (1.0324 - 0.19077 * Math.log10(waist - neck) + 0.15456 * Math.log10(height)) - 450;
    } else {
      bodyFatPercentage = 495 / (1.29579 - 0.35004 * Math.log10(waist + hip - neck) + 0.221 * Math.log10(height)) - 450;
    }
  
    bodyFatPercentage = bodyFatPercentage.toFixed(2);
  
    // Determine fat category
    let fatCategory = '';
    if (gender === 'male') {
      if (bodyFatPercentage < 6) fatCategory = 'Essential Fat';
      else if (bodyFatPercentage < 14) fatCategory = 'Athlete';
      else if (bodyFatPercentage < 18) fatCategory = 'Fitness';
      else if (bodyFatPercentage < 25) fatCategory = 'Average';
      else fatCategory = 'Obese';
    } else {
      if (bodyFatPercentage < 14) fatCategory = 'Essential Fat';
      else if (bodyFatPercentage < 21) fatCategory = 'Athlete';
      else if (bodyFatPercentage < 25) fatCategory = 'Fitness';
      else if (bodyFatPercentage < 32) fatCategory = 'Average';
      else fatCategory = 'Obese';
    }
  
    document.getElementById('fatResult').innerHTML = `Your Body Fat Percentage is ${bodyFatPercentage}% (${fatCategory}).`;
  
    // Adjust diet plan based on fat category
    let dietPlan = '';
    if (fatCategory === 'Essential Fat' || fatCategory === 'Athlete') {
      dietPlan = 'Maintain your fitness with a balanced diet and proper hydration.';
    } else if (fatCategory === 'Fitness') {
      dietPlan = 'Focus on high-protein, nutrient-rich foods to maintain your level.';
    } else if (fatCategory === 'Average') {
      dietPlan = 'Incorporate a calorie-controlled, nutrient-dense diet with exercise.';
    } else {
      dietPlan = 'Consult a healthcare provider for a personalized plan to reduce body fat.';
    }
  
    document.getElementById('dietPlan').innerHTML = `<p><strong>Recommended Diet:</strong> ${dietPlan}</p>`;
  }
  
  // Show/hide hip input for females
  document.getElementById('gender').addEventListener('change', function () {
    const gender = document.getElementById('gender').value;
    const hipLabel = document.getElementById('hipLabel');
    const hipInput = document.getElementById('hip');
    if (gender === 'female') {
      hipLabel.style.display = 'block';
      hipInput.style.display = 'block';
    } else {
      hipLabel.style.display = 'none';
      hipInput.style.display = 'none';
    }
  });
  