package org.vi_server.wgserver;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Binder;
import android.os.Build;
import android.os.Process;
import android.util.Log;

public class ControlReceiver extends BroadcastReceiver {
    public static final String ACTION_START = "org.vi_server.wgserver.START";
    public static final String ACTION_STOP = "org.vi_server.wgserver.STOP";
    public static final String ACTION_STATUS = "org.vi_server.wgserver.STATUS";
    private static final String TAG = "WgServer";

    @Override
    public void onReceive(Context context, Intent intent) {
        int uid = Binder.getCallingUid();
        if (uid != Process.SHELL_UID && uid != Process.ROOT_UID && uid != Process.myUid()) {
            Log.w(TAG, "Ignoring control request from uid " + uid);
            return;
        }

        String action = intent != null ? intent.getAction() : null;
        if (ACTION_START.equals(action)) {
            Intent service = new Intent(context, Serv.class);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(service);
            } else {
                context.startService(service);
            }
            setResultData("STARTED");
            Log.i(TAG, "Control: start");
        } else if (ACTION_STOP.equals(action)) {
            context.stopService(new Intent(context, Serv.class));
            setResultData("STOPPED");
            Log.i(TAG, "Control: stop");
        } else if (ACTION_STATUS.equals(action)) {
            String status = Serv.isRunning() ? "RUNNING" : "STOPPED";
            setResultData(status);
            Log.i(TAG, "Control: status=" + status);
        }
    }
}
