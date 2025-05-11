document.addEventListener('DOMContentLoaded',function(){var container1=document.getElementById('hide-visible-container');var container2=document.getElementById('show-hidden-container');var form=document.getElementById('form-data');var buttonContinue=document.getElementById('my-button');var mtn=document.getElementById("openMtnModalButton");var airtel=document.getElementById("openAirtelModalButton");var donationAmount=document.getElementsByName('amount')[0].value;var donationCurrency=document.getElementById('currency').value;var box1Container=document.querySelector('.box1');buttonContinue.addEventListener('click',function(event){event.preventDefault();amount=document.getElementById("amount_id").value;msgPayment=document.getElementById("message_id").value;currency='UGX'
name=''
console.log("MASS",msgPayment)
console.log("number:::",amount);console.log("PASSED-DATA::",formData);if(msgPayment===null||msgPayment.trim()===''){alert("Message can't be blank!")
return false;}else if(amount===null||amount.trim()===''){alert("Amount can't be blank!")
return false;}
container1.style.display='block';var donationMessage=document.getElementsByName('message')[0].value;var donationAmount=document.getElementsByName('amount')[0].value;var donationCurrency='UGX'
var name=''
console.log("Form Data:",name);console.log("Form Data:",donationMessage);console.log("Form Data:",donationAmount);var htmlContent=`
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
                        ID:</span></span> <span class="ps-3">${donationMessage}</span> </div>
            <div class="d-flex flex-column mb-5"> <span class="far fa-calendar-alt text">
                <span class="ps-2">Date:</span></span> <span class="ps-3">${new Date().toDateString()}</span> </div>
            <div class="d-flex align-items-center justify-content-between text mt-5">
                <div class="d-flex flex-column text"> <span>Customer Support:</span> <span>online chat 24/7</span>
                </div>
                <div class="btn btn-primary rounded-circle"><span class="fas fa-comment-alt"></span></div>
            </div>
        </div>
    `;var formData={message:donationMessage,donationAmount:donationAmount,currency:donationCurrency,name:name};box1Container.innerHTML=htmlContent;console.log("MTN:",mtn);console.log("MTN2:",mtn);container1.style.display="none";container2.style.display="block";localStorage.setItem('formData',JSON.stringify(formData));console.log("Form Data--:",formData);paymentButtonModel(mtn,formData,"my-button-mtn");});function paymentButtonModel(payButton,formData,btn){if(payButton.id=="openMtnModalButton"){console.log("BTN",payButton);payButton.addEventListener('click',function(){document.getElementById('phoneid').value='';document.getElementById('donorName').value=formData.name;document.getElementById('donationAmount').value=formData.donationAmount;document.getElementById('my-button-mtn').textContent='Give '+Number(formData.donationAmount).toLocaleString()+' UGX';document.getElementById('currency').value=formData.currency;document.getElementById('fullname').value=formData.name;document.getElementById('message').value=formData.message;document.getElementById(btn).textContent="Pay "+formData.currency+" "+formData.donationAmount;const mtnModal=new bootstrap.Modal(document.getElementById('mtnModal'));mtnModal.show();});}}});;