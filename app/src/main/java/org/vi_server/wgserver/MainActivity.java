package org.vi_server.wgserver;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Context ctx = this;
        EditText configText = findViewById(R.id.tConfig);

        String savedConfig = ConfigStore.load(ctx);
        if (savedConfig != null) {
            configText.setText(savedConfig);
        }

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
                ConfigStore.save(ctx, config);
                intent.putExtra("instance", instance);

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    ctx.startForegroundService(intent);
                } else {
                    ctx.startService(intent);
                }
                s.setText("started");
            }
        });

        b = findViewById(R.id.bStop);
        b.setOnClickListener(view -> {
            TextView s = findViewById(R.id.tStatus);
            ctx.stopService(new Intent(ctx, Serv.class));
            s.setText("stopped");
        });

        b = findViewById(R.id.bSampleConfig);
        b.setOnClickListener(view -> configText.setText(Native.getSampleConfig()));
    }
}
