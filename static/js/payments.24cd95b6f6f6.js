
document.addEventListener("DOMContentLoaded", function () {
    const closebtn = document.getElementById('btn-close').addEventListener('click', function(){
     const pendingModal = new bootstrap.Modal(document.getElementById('pendingModalLong'));
     pendingModal.hide();
     document.querySelector('.modal-backdrop')?.remove();

    });


     // Initialize modal and progress elements
  var modalProgressBar = document.getElementById('modalProgressBar');
  var btnCancel = document.getElementById('cancelbtn');
  var btnSuccess = document.getElementById('successbtn');
  var statusMessage = document.getElementById('statusMessage');

  var progress = 0;


    const form = document.getElementById('mtn-payment');

 
  // Disable the success button initially
  //btnSuccess.setAttribute('enable', true);
  
  // Update progress bar function
  function updateModalProgress() {
    if (progress < 100) {
      progress += 5;
      modalProgressBar.style.width = progress + '%';
      modalProgressBar.setAttribute('aria-valuenow', progress);
      modalProgressBar.innerHTML = progress + '%';
    }

    // When progress reaches 100%
    if (progress === 100) {
      statusMessage.innerHTML = "Transaction Successful!. Thank you for your donation!";
      btnSuccess.removeAttribute('disabled');
    }
  }

  // Show the modal and start the progress bar update
  function showModalAndStartProgress() {
    // Show the modal
    push.show();

    // Start the interval to update progress
    var intervalId = setInterval(updateModalProgress, 600); // Update every 600ms (0.6 seconds)

    // Optional: Stop polling after 60 seconds
    setTimeout(function() {
      clearInterval(intervalId);  // Stop polling after 60 seconds
      alert("Payment status check timed out after 60 seconds.");
      modalpush.hide(); // Optionally, hide the modal if the process timed out
    }, 60000); // Timeout after 60 seconds
  }


      var  mtnbutton = document.getElementById("my-button-mtn");
      const modalElement = document.getElementById('mtnModal');
      current_user = document.getElementById('donorName').value;
       var formData = JSON.parse(localStorage.getItem('formData')) || {};

     
       
       console.log("PASSED-DATA:--::",formData);
       
       const modalPendingElement = document.getElementById('pendingModalLong'); // The pending modal element
       const modalSuccessElement = document.getElementById('exampleModalPush'); // The success modal element


          // Initialize modals
   
    const modal =  new bootstrap.Modal(modalElement);
    const modalPending =  new bootstrap.Modal(modalPendingElement) ;
    const modalSuccess = new bootstrap.Modal(modalSuccessElement);
    const btnSuccess = document.getElementById('successbtn');
    var bsModal = new bootstrap.Modal(document.getElementById('myDialog'));
       
       //form = document.getElementById("payform");
     
     
       mtnbutton.addEventListener('click', function(event){
           event.preventDefault();
           number = document.getElementById("phoneid").value;
     
           msgPayment = document.getElementById("message").value;
           currency = document.getElementById('currency').value
     
           console.log("MASS---",msgPayment)
     
           console.log("number:::",number);
          // console.log(number === null);
          console.log("PASSED-DATA::",formData);
     
       if(number === null || number.trim() === '' ){
           alert("Phone number can't be blank!")
           return false;
       } // Check if the currency is selected (not the default value)
       else if (currency === '' || currency === 'Choose') {  // Assuming 'Choose' is the default value in the select box
           alert("Please select a valid currency.");
           return false;
       }else if (number !== '' && !number.match(/^\d{10,15}$/)){
           alert('Please enter a valid number.'); 
           return false; 
       }else{
               // If the number is valid, allow the form to be submitted
              // form.submit();

              if (number.startsWith('0')) {
                number = '256' + number.slice(1);
            }

              console.log("MASS",msgPayment)

              var phoneNumber = document.getElementById('phoneid').value.startsWith('0') 
              ? '256' + document.getElementById('phoneid').value.substring(1) 
              : document.getElementById('phoneid').value;

              const fullname = document.getElementById('fullname');
              
              var mtn_payment = {
               amount: document.getElementById('donationAmount').value,
               currency:currency,
               fullname:document.getElementById('donorName').value,
               message: document.getElementById('message').value,
               phone: phoneNumber,
              }
              
     
              data  ={
               "amount": mtn_payment['amount'],
               "currency": mtn_payment["currency"],
               "txt_ref": "some_ref_value",
               "phone_number": mtn_payment["phone"],
               "payermessage":mtn_payment["message"],
              }
              console.log("Data:MTN--M",data);
             
             
              
            // Hide the main modal (if it's visible) and show the pending modal
          // modal.hide();  // Hide the main modal
          // modalPending.show();  // Show the pending modal

          //modalPendings.show();

           // apiCall(data)
           const mtnModalInstance = bootstrap.Modal.getInstance(document.getElementById('mtnModal'));
           mtnModalInstance.hide();
           
           setTimeout(() => {
             const pendingModal = new bootstrap.Modal(document.getElementById('pendingModalLong'));
             pendingModal.show();
           }, 500); // matches Boot

            //  document.getElementById('myDialog').showModal();
            
            apiCall(data)
       
       } 
     
     });
     let intervalId; 

     function apiCall(data){
      const url = "https://pay.yeshualifeug.com/pay";
    
      fetch(url,
      { 
      method: "POST",
      headers: {
          'Content-Type': 'application/json'
      },
      body: JSON.stringify(
          {
              "amount": data['amount'] ,
              "currency": data['currency'],
              "txt_ref": data['txt_ref'],
              "phone_number": data['phone_number'],
              "payermessage": data['payermessage']
          })
      })
          .then( response => {
              //response => response.json()
    
              if(!response.ok){
                  return Promise.reject("API call failed with status: " + response.status);
              }
              return response.json();
          })  // Parse the response JSON
          .then(data => {
              console.log('API Response:', data);
           
              if (data.status === 'SUCCESSFUL') {
                 //alert('Payment processed successfully!');
                  //modalSuccess.hide();
               
              } else if (data.status === 'FAILED') {
                  alert('Payment failed: ' + data.message);
                  console.log('Payment failed:', data.message);
              } else if (data.status === 'PENDING') {
                  //alert('Payment is pending, please wait...');
                  console.log("Payment is pending, please wait...")
                  console.log("Response: Data", data)
              
                  console.log("Ref",data.ref);
                  pollPaymentStatus(data.ref);
              }
            
          })
          .catch(error => {
              console.error('Error calling /pay API:', error);
              alert('There was an error processing your payment.');
          });
    
    }


     // Polling function for payment status (this can be adjusted or omitted)
     function pollPaymentStatus(ref) {
      const intervalId =  setInterval(function () {
          fetch(`https://pay.yeshualifeug.com/status/${ref}`)
          .then(response => response.json())
          .then(data => {
              console.log('STATUS-PAY:', data.status);
              
              if (data.status === 'SUCCESSFUL') {
                  modalPending.hide(); // Hide pending modal
                  const peningModalInstance = bootstrap.Modal.getInstance(document.getElementById('pendingModalLong'));
                  peningModalInstance.hide()

                  setTimeout(() => {
                    modalSuccess.show();
                  }, 500);
                  // Show success modal
                  console.log("Payment processed successfully!")
                   clearInterval(intervalId); 
                  // alert("Payment was successful!");

              } else if (data.status === 'FAILED') {
                 
                  modalPending.hide(); // Optionally hide the pending modal
                  clearInterval(intervalId); 
                  alert("Payment failed: " + data.message);

              } else if (data.status === 'PENDING') {
                  console.log("Payment is still pending...");
                  modalPending.show()
              }
          })
          .catch(error => {
              console.error('Error polling payment status:', error);
          });
      }, 5000); // Poll every 5 seconds

          // Stop the polling after 60 seconds
    setTimeout(function () {
      clearInterval(intervalId);  // Stop polling after 60 seconds

      const pendingModal = bootstrap.Modal.getInstance(document.getElementById('pendingModalLong'));
      if (pendingModal) pendingModal.hide();
  
      const showsuccess = bootstrap.Modal.getInstance(document.getElementById('exampleModalPush'));
      if (showsuccess) showsuccess.hide();
      
      
        // Give modals a moment to hide before showing alert
    setTimeout(() => {
      alert("Payment status check timed out after 60 seconds.");
  }, 300);

      modalPending.hide(); // Optionally, hide the pending modal
  }, 50000); // 
  }




    });
