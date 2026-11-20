// =================================
// CIVIC EYE - PHOTO PREVIEW
// =================================

const photoInput = document.getElementById("photo");
const photoPreview = document.getElementById("photoPreview");

if (photoInput && photoPreview) {

    photoInput.addEventListener("change", function () {

        const file = photoInput.files[0];

        photoPreview.src = "";
        photoPreview.classList.remove("visible");

        if (!file) {
            return;
        }

        const allowedTypes = [
            "image/jpeg",
            "image/png",
            "image/webp"
        ];

        // Check file type
        if (!allowedTypes.includes(file.type)) {
            alert("Please choose a JPG, PNG or WEBP photo.");
            photoInput.value = "";
            return;
        }

        // Check 5 MB file limit
        if (file.size > 5 * 1024 * 1024) {
            alert("Photo must be 5 MB or smaller.");
            photoInput.value = "";
            return;
        }

        // Show preview
        const imageURL = URL.createObjectURL(file);
        photoPreview.src = imageURL;
        photoPreview.classList.add("visible");
    });
}


// =================================
// CIVIC EYE - GPS LOCATION
// =================================

const locationButton = document.getElementById("locationButton");

if (locationButton) {

    locationButton.addEventListener("click", function () {

        const message = document.getElementById("locationMessage");
        const latitudeField = document.getElementById("latitude");
        const longitudeField = document.getElementById("longitude");

        // Check browser GPS support
        if (!navigator.geolocation) {
            message.textContent =
                "GPS is not supported by this browser.";
            return;
        }

        message.textContent = "Getting your location...";

        navigator.geolocation.getCurrentPosition(

            // Success
            function (position) {

                latitudeField.value = position.coords.latitude;
                longitudeField.value = position.coords.longitude;

                message.textContent =
                    "Location captured successfully!";

            },

            // Error
            function (error) {

                if (error.code === 1) {
                    message.textContent =
                        "Location permission denied. You can enter the address manually.";
                } else if (error.code === 2) {
                    message.textContent =
                        "Location unavailable. Please try again.";
                } else if (error.code === 3) {
                    message.textContent =
                        "Location request timed out. Try again.";
                } else {
                    message.textContent =
                        "Could not get location. You can still submit.";
                }

            },

            // GPS settings
            {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 0
            }

        );
    });
}