package com.weartak.plugin.template.ui

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.weartak.plugin.sdk.WearTakPluginContract
import com.weartak.plugin.appteamplate.R

/**
 * External settings entry (action [WearTakPluginContract.ACTION_PLUGIN_SETTINGS]).
 * Hosted settings are preferred in v1; this activity remains a hook for tooling.
 */
class TemplateSettingsActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val tv = TextView(this).apply {
            text = getString(R.string.template_settings_hint, WearTakPluginContract.ACTION_PLUGIN_SETTINGS)
            setPadding(48, 48, 48, 48)
        }
        setContentView(tv)
    }
}
