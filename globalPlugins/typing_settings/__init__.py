import nvwave
import globalPluginHandler
import speech
import config
import os
import glob
import wx
import addonHandler
import api
from random import randint
from globalCommands import SCRCAT_CONFIG
from ui import message
from scriptHandler import script
from gui import SettingsPanel, NVDASettingsDialog, guiHelper
from controlTypes import STATE_READONLY, STATE_EDITABLE
def confinit():
	confspec = {
		"typingsnd": "boolean(default=true)",
		"typing_sound": f"string(default={get_sounds_folders()[0]})",
		"speak_characters": "integer(default=0)",
		"speak_words": "integer(default=0)",
		"speak_command_keys": "integer(default=0)",
		"speak_on_protected":"boolean(default=False)"}
	config.confspec["typing_settings"] = confspec

addonHandler.initTranslation()
effects_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "effects")
controls = (8, 52, 82)
typingProtected = api.isTypingProtected

def get_sounds_folders():
		return os.listdir(effects_dir)

def get_sounds(name):
	return [os.path.basename(sound) for sound in glob.glob(f"{effects_dir}/{name}/*.wav")]

def RestoreTypingProtected():
	api.isTypingProtected = typingProtected

def IsTypingProtected():
	if config.conf["typing_settings"]["speak_on_protected"]:
		return False
	focus = api.getFocusObject()
	if focus.isProtected:
		return True

confinit()
class TypingSettingsPanel(SettingsPanel):
	title = _("typing settings")
	def makeSettings(self, settingsSizer):
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		self.tlable = sHelper.addItem(wx.StaticText(self, label=_("typing sound:"), name="ts"))
		self.typingSound = sHelper.addItem(wx.Choice(self, name="ts"))
		sounds = get_sounds_folders()
		self.typingSound.Set(sounds)
		self.typingSound.SetStringSelection(config.conf["typing_settings"]["typing_sound"])
		self.slable = sHelper.addItem(wx.StaticText(self, label=_("sounds"), name="ts"))
		self.sounds = sHelper.addItem(wx.Choice(self, name="ts"))
		sHelper.addItem(wx.StaticText(self, label=_("speek characters")))
		self.speakCharacters = sHelper.addItem(wx.Choice(self, choices=[_("off"), _("anywhere"), _("in edit boxes only")]))
		sHelper.addItem(wx.StaticText(self, label=_("speek command keys")))
		self.speakCommandKeys = sHelper.addItem(wx.Choice(self, choices=[_("off"), _("anywhere"), _("in edit boxes only")]))
		sHelper.addItem(wx.StaticText(self, label=_("speak words")))
		self.speakWords = sHelper.addItem(wx.Choice(self, choices=[_("off"), _("anywhere"), _("in edit boxes only")]))
		self.playTypingSounds = sHelper.addItem(wx.CheckBox(self, label=_("play sounds while typing")))
		self.playTypingSounds.SetValue(config.conf["typing_settings"]["typingsnd"])
		self.speakPasswords = sHelper.addItem(wx.CheckBox(self, label=_("speak passwords")))
		self.speakPasswords.SetValue(config.conf["typing_settings"]["speak_on_protected"])
		try:
			self.speakCharacters.SetSelection(config.conf["typing_settings"]["speak_characters"])
		except:
			self.speakCharacters.SetSelection(0)
		try:
			self.speakCommandKeys.SetSelection(config.conf["typing_settings"]["speak_command_keys"])
		except:
			self.speakCommandKeys.SetSelection(0)
		try:
			self.speakWords.SetSelection(config.conf["typing_settings"]["speak_words"])
		except:
			self.speakWords.SetSelection(0)
		self.OnChangeTypingSounds(None)
		self.onChange(None)
		self.playTypingSounds.Bind(wx.EVT_CHECKBOX, self.OnChangeTypingSounds)
		self.typingSound.Bind(wx.EVT_CHOICE, self.onChange)
		self.sounds.Bind(wx.EVT_CHOICE, self.onPlay)

	def postInit(self):
		self.typingSound.SetFocus()

	def OnChangeTypingSounds(self, evt):
		for obj in self.GetChildren():
			if obj.Name == "ts": obj.Hide() if not self.playTypingSounds.GetValue() else obj.Show()

	def onChange(self, event):
		sounds = get_sounds(self.typingSound.GetStringSelection())
		self.sounds.Set(sounds)
		try:
			self.sounds.SetSelection(0)
		except: pass

	def onPlay(self, event):
		nvwave.playWaveFile(f"{effects_dir}/{self.typingSound.GetStringSelection()}/{self.sounds.GetStringSelection()}", True)

	def onSave(self):
		config.conf["typing_settings"]["typing_sound"] = self.typingSound.GetStringSelection()
		config.conf["typing_settings"]["speak_characters"] = self.speakCharacters.GetSelection()
		config.conf["typing_settings"]["speak_command_keys"] = self.speakCommandKeys.GetSelection()
		config.conf["typing_settings"]["speak_words"] = self.speakWords.GetSelection()
		config.conf["typing_settings"]["speak_on_protected"] = self.speakPasswords.GetValue()
		config.conf["typing_settings"]["typingsnd"] = self.playTypingSounds.GetValue()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		NVDASettingsDialog.categoryClasses.append(TypingSettingsPanel)

	def IsEditable(self, object):
		return (object.role in controls or STATE_EDITABLE in object.states) and not STATE_READONLY in object.states

	def event_gainFocus(self, object, nextHandler):
		if config.conf["typing_settings"]["speak_characters"] ==2:
			config.conf["keyboard"]["speakTypedCharacters"] = self.IsEditable(object)
		if config.conf["typing_settings"]["speak_command_keys"] ==2:
			config.conf["keyboard"]["speakCommandKeys"] = self.IsEditable(object)
		if config.conf["typing_settings"]["speak_words"] == 2:
			config.conf["keyboard"]["speakTypedWords"] = self.IsEditable(object)
		api.isTypingProtected = IsTypingProtected
		nextHandler()

	def event_typedCharacter(self, obj, nextHandler, ch):
		if self.IsEditable(obj) and config.conf["typing_settings"]["typingsnd"]:
			if ch ==" ":
				nvwave.playWaveFile(os.path.join(effects_dir, config.conf['typing_settings']['typing_sound'], "space.wav"), True)
			elif ch == "\b":
				nvwave.playWaveFile(os.path.join(effects_dir, config.conf['typing_settings']['typing_sound'], "delete.wav"), True)
			else:
				count = self.SoundsCount(config.conf["typing_settings"]["typing_sound"])
				if (count<=0):
					nvwave.playWaveFile(os.path.join(effects_dir, config.conf['typing_settings']['typing_sound'], "typing.wav"), True)
				else:
					nvwave.playWaveFile(os.path.join(effects_dir, config.conf['typing_settings']['typing_sound'], "typing_"+str(randint(1, count))+".wav"), True)
		nextHandler()

	def SoundsCount(self, name):
		path = f"{effects_dir}/{name}"
		files = len([file for file in os.listdir(path) if file.startswith("typing_")])
		return files


	@script(
		description = _("Enable and disable typing sounds"),
		category=_("typing settings"),
		gestures=["kb:nvda+shift+k"])
	def script_toggle_typing_sounds(self, gesture):
		current = config.conf["typing_settings"]["typingsnd"]
		if current:
			config.conf["typing_settings"]["typingsnd"] = False
			message(_("typing sounds off"))
		else:
			config.conf["typing_settings"]["typingsnd"] = True
			message(_("typing sounds on"))

	@script(
		description = _("Enable or disable speak passwords"),
		category = _("typing settings"),
		gestures = ["kb:nvda+shift+p"])
	def script_toggle_speak_passwords(self, gesture):
		if config.conf["typing_settings"]["speak_on_protected"]:
			config.conf["typing_settings"]["speak_on_protected"] = False
			message(_("speak passwords off"))
		else:
			config.conf["typing_settings"]["speak_on_protected"] = True
			message(_("speak passwords on"))

	@script(
		description = _("Switches between the available speak characters  modes."),
		category = _("typing settings"),
gestures=["kb:nvda+2"])
	def script_speak_characters(self, gesture):
		current = config.conf["typing_settings"]["speak_characters"]
		if current >=2:
			current = 0
			config.conf["keyboard"]["speakTypedCharacters"] = False
			message(_("speak typed characters off"))
		else:
			current +=1
			if current == 1:
				config.conf["keyboard"]["speakTypedCharacters"] = True
				message(_("speak typed characters anywhere"))
			elif current == 2:
				message(_("speak typed characters in edit boxes only"))
		config.conf["typing_settings"]["speak_characters"] = current

	@script(
		description = _("Switches between the available speak words  modes."),
		category = _("typing settings"),
gestures=["kb:nvda+3"])
	def script_speak_words(self, gesture):
		current = config.conf["typing_settings"]["speak_words"]
		if current >=2:
			current = 0
			config.conf["keyboard"]["speakTypedWords"] = False
			message(_("speak typed words off"))
		else:
			current +=1
			if current == 1:
				config.conf["keyboard"]["speakTypedWords"] = True
				message(_("speak typed words anywhere"))
			elif current == 2:
				message(_("speak typed words in edit boxes only"))
		config.conf["typing_settings"]["speak_words"] = current

	@script(
		description = _("Switches between the available speak command keys modes."),
		category = _("typing settings"),
gestures=["kb:nvda+4"])
	def script_speak_command_keys(self, gesture):
		current = config.conf["typing_settings"]["speak_command_keys"]
		if current >=2:
			current = 0
			config.conf["keyboard"]["speakCommandKeys"] = False
			message(_("speak command keys off"))
		else:
			current +=1
			if current == 1:
				config.conf["keyboard"]["speakCommandKeys"] = True
				message(_("speak typed Command Keys anywhere"))
			elif current == 2:
				message(_("speak Command Keys in edit boxes only"))
		config.conf["typing_settings"]["speak_command_keys"] = current

	def terminate(self):
		RestoreTypingProtected()
		NVDASettingsDialog.categoryClasses.remove(TypingSettingsPanel)
