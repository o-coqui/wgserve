package org.vi_server.wgserver;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final String PREFS_NAME = "wgserve_prefs";
    private static final String CONFIG_KEY = "config";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Context ctx = this;
        EditText configText = findViewById(R.id.tConfig);

        // Restore the last successfully started configuration after app/process/reboot.
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        String savedConfig = prefs.getString(CONFIG_KEY, null);
        if (savedConfig != null) {
            configText.setText(savedConfig);
        }

        {
            Button b = findViewById(R.id.bStart);
            b.setOnClickListener(view -> {
                Intent intent = new Intent(ctx, Serv.class);

                String config = configText.getText().toString();

                long instance = Native.create();
                String ret = Native.setConfig(instance, config);

                TextView s = findViewById(R.id.tStatus);
                if (ret != null && !ret.isEmpty()) {
                    s.setText(ret);
                    Native.destroy(instance);
                } else {
                    // Persist only a configuration that was accepted by the native parser.
                    prefs.edit().putString(CONFIG_KEY, config).apply();

                    intent.putExtra("instance", instance);

                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        ctx.startForegroundService(intent);
                    } else {
                        ctx.startService(intent);
                    }
                    s.setText("started");
                }
            });
        }
        {
            Button b = findViewById(R.id.bStop);
            b.setOnClickListener(view -> {
                TextView s = findViewById(R.id.tStatus);
                Intent intent = new Intent(ctx, Serv.class);
                ctx.stopService(intent);
                s.setText("stopped");
            });
        }

        {
            Button b = findViewById(R.id.bSampleConfig);
            b.setOnClickListener(view -> {
                configText.setText(Native.getSampleConfig());
            });
        }
    }
}
