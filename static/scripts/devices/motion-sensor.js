var MotionSensor = (function () {
    'use strict';
    
    //Constructor
    function MotionSensor( mqtt_publish_topic, state )
    {
        MqttDevice.call( this, mqtt_publish_topic, state );
    }
    
    MotionSensor.prototype = Object.create( MqttDevice.prototype );
    MotionSensor.prototype.constructor = MotionSensor;

    return MotionSensor;
})();
