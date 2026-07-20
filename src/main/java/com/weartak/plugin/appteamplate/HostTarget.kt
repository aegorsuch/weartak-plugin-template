package com.weartak.plugin.appteamplate

object HostTarget {
    val hostPackageName: String?
        get() = com.weartak.plugin.template.service.TemplatePluginRuntime.currentSnapshot().hostPackageName
}
