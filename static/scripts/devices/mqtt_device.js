function State(stringList) {
    // Loop through the list of strings
    for (var i = 0; i < stringList.length; i++) {
        // Add each string as a property of the object
        this[stringList[i]] = 'UNAVAILABLE';
    }
}

// Define the Update method for State
State.prototype.Update = function(jsonObj) {
    // Loop through the properties of the JSON object
    for (var prop in jsonObj) {
        // Check if the property exists in the StringObject
        if (this.hasOwnProperty(prop)) {
            // Update the property value
            this[prop] = jsonObj[prop];
        }
    }
};

function Device( mqtt_subscribe_topic, mqtt_publish_topic, cameraId, videostream, state, detection )
{
    this.id = generateUUID();
    // console.log( 'New Device ', this, ' created' );
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0,
            v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

Device.prototype.equals = function( device )
{    
    return this.id == device.id
}

function MqttDevice( mqtt_publish_topic, state, mqtt_subscribe_topic )
{
    Device.call( this );

    this.mqtt_subscribe_topic = mqtt_subscribe_topic;
    this.mqtt_publish_topic = typeof mqtt_publish_topic !== 'undefined' ? mqtt_publish_topic : null;
    this.state = state;
    this.lastUpdateDate = '-';  // ATTENTION: items are proxied to trigger ui update when a property
                                // changes. Date proeprties do not work with proxies therefore
                                // date properties must be stored as string and for manipulation
                                // converted back and forth between Date object and string
    this.publisher = null;
    this.mqtt_message = ""; //store the incoming raw mqtt messages as strings for debugging
}

MqttDevice.prototype = Object.create( Device.prototype );
MqttDevice.prototype.constructor = MqttDevice;

MqttDevice.prototype.update = function( topic, message )
{
    if( topic == this.mqtt_publish_topic )
    {
        // console.log( 'MqttDevice[' + this.mqtt_publish_topic +']: this message is for me.' );
        try
        {            
            this.state.Update( JSON.parse( message ) );
            // console.log("state now: ", this.state);
            this.lastUpdateDate = new Date().toLocaleString();
            this.mqtt_message = message;
            return true;
        }
        catch( error )
        {
            console.error( error );
            return false;
        }
    }
    return false;
}

MqttDevice.prototype.setPublisher = function( publisher )
{
    this.publisher = publisher;
}