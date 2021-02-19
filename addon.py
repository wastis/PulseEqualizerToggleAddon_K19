import xbmc
import xbmcaddon
import xbmcgui
import sys, os

addon      = xbmcaddon.Addon()
addonname  = addon.getAddonInfo('name')
cwd        = addon.getAddonInfo('path')

if sys.version_info[0] > 2:
	resource   = xbmc.translatePath( os.path.join( cwd, 'resources', 'lib' ))
else:
	resource   = xbmc.translatePath( os.path.join( cwd, 'resources', 'lib' )).decode("utf-8")

sys.path.append (resource)

import dbussy as dbus
from dbussy import DBUS

manager_path='/org/pulseaudio/equalizing1'
manager_iface='org.PulseAudio.Ext.Equalizing1.Manager'
equalizer_iface='org.PulseAudio.Ext.Equalizing1.Equalizer'
device_iface='org.PulseAudio.Core1.Device'

#
#define some basic dbus functin calls
#

def print_introspect(interface, d_path ):
	request = dbus.Message.new_method_call(
		destination = dbus.valid_bus_name(interface),
		path = d_path,
		iface = DBUS.INTERFACE_INTROSPECTABLE,
		method = "Introspect"
	)

	reply = conn.send_with_reply_and_block(request)
	sys.stdout.write(reply.expect_return_objects("s")[0])
	
def get_property(interface, d_path, p_name):
	request = dbus.Message.new_method_call (
		destination = dbus.valid_bus_name(interface),
		path = d_path,
		iface = DBUS.INTERFACE_PROPERTIES,
		method = "Get"
	)
	request.append_objects("ss", dbus.valid_interface(interface),p_name)
	reply = conn.send_with_reply_and_block(request)

	return reply.expect_return_objects("v")[0]
	
def call_func(interface, d_path, func, *args):
	request = dbus.Message.new_method_call (
		destination = dbus.valid_bus_name(interface),
		path = d_path,
		iface = dbus.valid_bus_name(interface),
		method = func
	)
	request.append_objects(*args)
	return conn.send_with_reply_and_block(request)


#
#	connect to equalizer
#
def connect():
	try:
		destination = 'org.PulseAudio1' 
		object_path = '/org/pulseaudio/server_lookup1' 
		interface_name = 'org.PulseAudio.ServerLookup1'

		conn = dbus.Connection.bus_get(DBUS.BUS_SESSION,private = False)

		request = dbus.Message.new_method_call (
			destination = dbus.valid_bus_name(destination),
			path = dbus.valid_path(object_path),
			iface = DBUS.INTERFACE_PROPERTIES,
			method = "Get"
		)
		
		request.append_objects("ss", dbus.valid_interface(interface_name),'Address')
		reply = conn.send_with_reply_and_block(request)

		address = reply.expect_return_objects("v")[0][1]
		
	except Exception as e:
		print('There was an error connecting to pulseaudio, '
						 'please make sure you have the pulseaudio dbus '
						 'module loaded, exiting...\n')
		sys.exit(-1)

	return dbus.Connection.open(address,0)



#
# Class Filter, to manage the equalizer settings to a given sink 
#

class Filter():
	def __init__(self,sink_path):
		self.sink_path = sink_path
		self.channel = get_property(equalizer_iface, sink_path, 'NChannels')[1]
	
	def load_profile(self,profile):
		call_func(equalizer_iface,self.sink_path,'LoadProfile',"us",self.channel,profile)
	
	def get_base_profile(self):
		return call_func(equalizer_iface,sink_path,'BaseProfile',"u", self.channel).expect_return_objects("s")[0]
		

#connect to eaqulizer
conn = connect()

#get profies list
profile_list =  get_property(manager_iface,manager_path, 'Profiles')[1]

#get the sink list
sinks = get_property(manager_iface,manager_path, 'EqualizedSinks')[1]

#only one sink supported yet
sink_path = sinks[0]

dialog = xbmcgui.Dialog()
selection = dialog.contextmenu(profile_list)

#initiate the Filter to the sink
f = Filter(sink_path)

#load the profile
f.load_profile(profile_list[selection])

xbmc.log("actual equalizer profile = "+f.get_base_profile(),xbmc.LOGINFO)
