var MotionSensor = (function () {
    'use strict';
    
    //Constructor
    function MotionSensor( mqtt_publish_topic, state )
    {
        MqttDevice.call( this, mqtt_publish_topic, state );

        this.activeONStatePeriod = 10000;   // in millisecs
    }
    
    MotionSensor.prototype = Object.create( MqttDevice.prototype );
    MotionSensor.prototype.constructor = MotionSensor;

    MotionSensor.prototype.update = function( topic, message )
    {
        const self = this; // Maintain reference to the MotionSensor object

        // define function to be called until activeONStatePeriod expires
        function calculateState()
        {
            if(self.state.main == 'OFF')
            {
                return;
            }

            // Add 'T' between date and time
            const isoStringWithT = self.lastUpdateDate.replace(' ', 'T');

            // Parse the ISO string with 'T' to a Date object
            const dateTime = new Date(isoStringWithT);

            // Get the current time
            const currentTime = new Date();

            // Calculate the difference in milliseconds
            const difference = currentTime - dateTime;
            // console.log("diff: ", difference)
            // Check if the difference is less than x milliseconds
            if(difference > self.activeONStatePeriod)
            {
                // console.log("MotionSensor state set to OFF.")
                self.state.main ='OFF';
            }
            else
            {
                // console.log("MotionSensor state still ON. Will recalculate in 1 sec")
                setTimeout(calculateState, 1000); // check again in a sec
            }
        }

        MqttDevice.prototype.update.call(this, topic, message);
        if(this.state.main == 'ON')
        {
            // console.log("MotionSensor state set to ON.")
            // Call the function recursively after a delay of 1 second
            setTimeout(calculateState, 1000);
        }
    }

    

    return MotionSensor;
})();
