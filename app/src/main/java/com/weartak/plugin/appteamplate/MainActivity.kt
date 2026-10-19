package com.weartak.plugin.appteamplate

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.weartak.plugin.template.service.TemplateActionOutcome
import com.weartak.plugin.template.service.TemplatePluginRuntime
import com.weartak.plugin.template.service.TemplatePluginSnapshot
import com.weartak.plugin.template.service.TemplatePluginSnapshotObserver
import kotlin.concurrent.thread

class MainActivity : AppCompatActivity() {

    private lateinit var statusView: TextView
    private lateinit var hostView: TextView

    private val snapshotObserver = TemplatePluginSnapshotObserver { snapshot ->
        runOnUiThread { renderSnapshot(snapshot) }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        statusView = TextView(this).apply {
            textSize = 16f
            setPadding(0, 12, 0, 12)
        }
        hostView = TextView(this).apply {
            textSize = 14f
            setPadding(0, 0, 0, 16)
        }

        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(40, 40, 40, 40)
            addView(TextView(this@MainActivity).apply {
                text = "WearTAK app template"
                textSize = 22f
            })
            addView(hostView)
            addView(statusView)
            addView(buildActionButton("CEP Add", TemplatePluginRuntime.ACTION_CEP_DEMO))
            addView(buildActionButton("CEP Remove", TemplatePluginRuntime.ACTION_CEP_DEMO, removeOperationArgs()))
            addView(buildActionButton("Settings", TemplatePluginRuntime.ACTION_SETTINGS_DEMO))
            addView(buildActionButton("Map Show", TemplatePluginRuntime.ACTION_MAP_DEMO))
            addView(buildActionButton("Map Remove", TemplatePluginRuntime.ACTION_MAP_DEMO, removeOperationArgs()))
            addView(buildActionButton("Alert", TemplatePluginRuntime.ACTION_ALERT_DEMO))
            addView(buildActionButton("Hello World", TemplatePluginRuntime.ACTION_HELLO_WORLD))
            addView(buildActionButton("Direct CoT", TemplatePluginRuntime.ACTION_COT_DEMO))
            addView(buildActionButton("Marker Publish", TemplatePluginRuntime.ACTION_MARKER_PUBLISH))
            addView(buildActionButton("Marker Update", TemplatePluginRuntime.ACTION_MARKER_UPDATE))
            addView(buildActionButton("Marker Clear", TemplatePluginRuntime.ACTION_MARKER_CLEAR))
            addView(buildActionButton("Device Status", TemplatePluginRuntime.ACTION_DEVICE_STATUS))
            addView(buildActionButton("Sensor Event", TemplatePluginRuntime.ACTION_SENSOR_EVENT))
            addView(buildActionButton("Sensor Batch", TemplatePluginRuntime.ACTION_SENSOR_BATCH))
            addView(buildActionButton("CoT Ready", TemplatePluginRuntime.ACTION_COT_READY))
            addView(buildActionButton("CoT Not Ready", TemplatePluginRuntime.ACTION_COT_READY, Bundle().apply {
                putBoolean("ready", false)
            }))
            addView(buildReturnButton())
        }

        setContentView(
            ScrollView(this).apply {
                addView(content)
            },
        )
        renderSnapshot(TemplatePluginRuntime.currentSnapshot())
    }

    override fun onStart() {
        super.onStart()
        renderSnapshot(TemplatePluginRuntime.addObserver(snapshotObserver))
    }

    override fun onStop() {
        TemplatePluginRuntime.removeObserver(snapshotObserver)
        super.onStop()
    }

    private fun buildActionButton(label: String, actionId: String, args: Bundle = Bundle()): Button =
        Button(this).apply {
            text = label
            setOnClickListener { executeAction(actionId, Bundle(args)) }
        }

    private fun buildReturnButton(): Button =
        Button(this).apply {
            text = "Return to WearTAK"
            setOnClickListener { openWearTak() }
        }

    private fun executeAction(actionId: String, args: Bundle = Bundle()) {
        thread(name = "WearTAK-action-$actionId") {
            val outcome = TemplatePluginRuntime.invokeMainUiAction(actionId, args)
            runOnUiThread { renderOutcome(outcome) }
        }
    }

    private fun renderOutcome(outcome: TemplateActionOutcome) {
        statusView.text = "${outcome.actionId}: ${outcome.message}"
        Toast.makeText(this, outcome.message, Toast.LENGTH_SHORT).show()
    }

    private fun renderSnapshot(snapshot: TemplatePluginSnapshot) {
        hostView.text = "Host package: ${snapshot.hostPackageName ?: "unknown"}"
        statusView.text = buildString {
            append("Lifecycle: ")
            append(snapshot.lifecycleState)
            append('\n')
            append("Attached: ")
            append(if (snapshot.attached) "yes" else "no")
            append('\n')
            append("Action: ")
            append(snapshot.lastActionId)
            append(" -> ")
            append(snapshot.lastActionMessage)
            append('\n')
            append("Counts: cep=")
            append(snapshot.cepRuns)
            append(" settings=")
            append(snapshot.settingsRuns)
            append(" map=")
            append(snapshot.mapRuns)
            append(" alert=")
            append(snapshot.alertRuns)
            append(" hello=")
            append(snapshot.helloRuns)
        }
    }

    private fun openWearTak() {
        val hostPackage = TemplatePluginRuntime.currentSnapshot().hostPackageName
        if (hostPackage.isNullOrBlank()) {
            Toast.makeText(this, "WearTAK host package unavailable", Toast.LENGTH_LONG).show()
            return
        }
        val launchIntent = packageManager.getLaunchIntentForPackage(hostPackage)
        if (launchIntent == null) {
            Toast.makeText(this, "Unable to launch WearTAK", Toast.LENGTH_LONG).show()
            return
        }
        startActivity(launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }

    private fun removeOperationArgs(): Bundle = Bundle().apply {
        putString("operation", "remove")
    }
}
