document.addEventListener('DOMContentLoaded', function() {
    var container1 = document.getElementById('hide-visible-container');
    var container2 = document.getElementById('show-hidden-container');
    var form = document.getElementById('form-data');
    var buttonContinue = document.getElementById('my-button');
    var mtn = document.getElementById("openMtnModalButton");
    var airtel = document.getElementById("openAirtelModalButton");
    var donationAmount = document.getElementsByName('amount')[0].value;
    var donationCurrency = document.getElementById('currency').value;


    var box1Container = document.querySelector('.summary-amount');
   // buttonContinue.innerHTML = donationAmount + donationCurrency
    buttonContinue.addEventListener('click', function(event) {
        event.preventDefault();


       // number = document.getElementById("phone_id").value;
        amount = document.getElementById("amount_id").value;
        msgPayment = document.getElementById("message_id").value;
        currency = 'UGX'//document.getElementById('currency').value
        name = ''//document.getElementById('name_id').value
  
        console.log("MASS",msgPayment)
  
        console.log("number:::",amount);
       // console.log(number === null);
       console.log("PASSED-DATA::",formData);

    if(msgPayment === null || msgPayment.trim() === '' ){
        alert("Message can't be blank!")
        return false;
    }else  if(amount === null || amount.trim() === '' ){
        alert("Amount can't be blank!")
        return false;
    }

   // Make sure container1 is visible before proceeding
    container1.style.display = 'block'; // Or apply your preferred style to make it visible

    // Get values from form inputs
    var donationMessage = document.getElementsByName('message')[0].value;
    var donationAmount = document.getElementsByName('amount')[0].value;
    var donationCurrency = 'UGX'//document.getElementById('currency').value;
    var name = ''//document.getElementsByName('fullname')[0].value;

        console.log("Form Data:", name);
        console.log("Form Data:", donationMessage);
        console.log("Form Data:", donationAmount);


      // Construct HTML content with collected data
        var htmlContent = `
        <div class="fw-bolder mb-4"><span class="ps-1">${Number(donationAmount).toLocaleString()}.00 UGX</span></div>
        <div class="d-flex flex-column">
            <div class="d-flex align-items-center justify-content-between text"> 
                <span class="">FullNames:</span>
                <span class="ps-1" id="usernameinfo">${name}</span> 
            </div>
            <div class="d-flex align-items-center justify-content-between text"> <span class="">Currency</span>
                <span class="fas fa-dollar-sign"><span class="ps-1">${donationCurrency}</span></span> </div>
            <div class="d-flex align-items-center justify-content-between text mb-4"> <span>Tax</span>
            <span class="ps-1">0</span></span> </div>
            <div class="border-bottom mb-4"></div>
            <div class="d-flex flex-column mb-4"> <span class="far fa-file-alt text"><span class="ps-2">Message
            :</span></span> <span class="ps-3">${donationMessage}</span> </div>
            <div class="d-flex flex-column mb-5">
           </div>
      
        </div>
    `;

            // Construct an object with collected data
             var formData = {
                    message: donationMessage,
                    donationAmount: donationAmount,
                    currency: donationCurrency,
                    name: name
                };

            // Update the HTML content of box1Container
            // box1Container.innerHTML = htmlContent;
            console.log("MTN:", mtn);
           // mtn["formData"] = formData;
            console.log("MTN2:", mtn);
        // Alert the user to confirm the action
            // Hide and show containers
            container1.style.display = "none";
            container2.style.display = "block";
          

            // Store the form data object in localStorage
            localStorage.setItem('formData', JSON.stringify(formData));

            console.log("Form Data--:", formData);

            
        

        paymentButtonModel(mtn,formData,"my-button-mtn");

        paymentButtonModel(airtel,formData,"airtel-pay-button");

        //console.log("MDC", formData); // This line will throw an error, formData is not accessible here
    });

    function paymentButtonModel(payButton,formData,btn){
        

        if(payButton.id == "openMtnModalButton"){
            console.log("BTN",payButton);
            payButton.addEventListener('click', function(){
                // Populate the form fields of the MTN modal with the form data
             document.getElementById('phoneid').value = ''; // Clear the phone input field
             document.getElementById('donorName').value = formData.name;
             document.getElementById('donationAmount').value = formData.donationAmount;
             document.getElementById('my-button-mtn').textContent = 'Give ' + Number(formData.donationAmount).toLocaleString() + ' UGX';
             document.getElementById('currency').value = formData.currency;
             document.getElementById('fullname').value = formData.name;
             document.getElementById('message').value = formData.message;
     
             // Set the button text with the amount
             document.getElementById(btn).textContent = 'Give ' + Number(formData.donationAmount).toLocaleString() + ' UGX';
             
            // button.textContent = "Pay "+ formData.currency + " "+ donationAmount;

           // document.getElementById('openMtnModalButton').addEventListener('click', function () {
                const mtnModal = new bootstrap.Modal(document.getElementById('mtnModal'));
                 mtnModal.show();
          
             // });


     
                 });

        }
        
        else if(payButton.id == "openAirtelModalButton"){
            console.log("BTN",payButton);
            payButton.addEventListener('click', function(){
                // Populate the form fields of the Airtel modal with the form data
             document.getElementById('airtel-pay-phoneid').value = ''; // Clear the phone input field
             document.getElementById('donorName').value = formData.name;
             document.getElementById('donationAmount').value = formData.donationAmount;
             document.getElementById('currency').value = formData.currency;
             document.getElementById('fullname').value = formData.name;
             document.getElementById('message').value = formData.message;
     
             // Set the button text with the amount
             document.getElementById(btn).textContent = 'Give ' + Number(formData.donationAmount).toLocaleString() + ' UGX';
             
            // button.textContent = "Pay "+ formData.currency + " "+ donationAmount;

            // Show the Airtel modal
            const airtelModal = new bootstrap.Modal(document.getElementById('airtelModal'));
            airtelModal.show();
     
                 });
        }

    }

});