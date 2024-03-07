var Door1 = (function () {
    'use strict';
    
    //Constructor
    function Window2R( mqtt_publish_topic, state )
    {
        //public properties
        MqttDevice.call( this, mqtt_publish_topic, state );
    }
    
    Window2R.prototype = Object.create( MqttDevice.prototype );
    Window2R.prototype.constructor = Window2R;

    return Window2R;
})();