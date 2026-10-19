package com.weartak.plugin.template.ui

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.weartak.plugin.sdk.WearTakPluginContract
import com.weartak.plugin.appteamplate.R

class TemplateMainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val tv = TextView(this).apply {
            text = getString(
                R.string.template_main_hint,
                WearTakPluginContract.ACTION_PLUGIN_SERVICE,
            )
            setPadding(48, 48, 48, 48)
        }
        setContentView(tv)
    }
}
