package xyz.smartuni.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DatePickerDialog;
import android.content.Intent;
import android.net.Uri;
import android.text.InputType;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.Calendar;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Primera experiencia nativa SMART UNI. Las secciones no implementadas no
 * muestran datos ficticios ni indican sincronización sin un ACK real.
 */
public final class MainActivity extends Activity {
    private static final int PRIMARY = Color.rgb(43, 128, 236);
    private static final int CTA = Color.rgb(43, 178, 196);
    private static final int TEXT = Color.rgb(36, 52, 72);
    private static final int MUTED = Color.rgb(101, 118, 140);
    private static final int BACKGROUND = Color.rgb(243, 247, 252);
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private LinearLayout mainContent;
    private String screen = "Inicio";

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        showScreen("Inicio");
    }

    private int dp(int size) {
        return (int) (size * getResources().getDisplayMetrics().density + .5f);
    }

    private GradientDrawable rounded(int color) {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(color);
        shape.setCornerRadius(dp(12));
        return shape;
    }

    private TextView text(String content, int size, int color, boolean bold) {
        TextView widget = new TextView(this);
        widget.setText(content);
        widget.setTextSize(size);
        widget.setTextColor(color);
        if (bold) widget.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        widget.setGravity(Gravity.CENTER_VERTICAL);
        return widget;
    }

    private void addSpacing(LinearLayout container, int height) {
        View spacer = new View(this);
        container.addView(spacer, new LinearLayout.LayoutParams(1, dp(height)));
    }

    private Button button(String title, Runnable action) {
        Button widget = new Button(this);
        widget.setText(title);
        widget.setAllCaps(false);
        widget.setTextColor(Color.WHITE);
        widget.setBackground(rounded(PRIMARY));
        widget.setOnClickListener(view -> action.run());
        return widget;
    }

    private void showScreen(String destination) {
        screen = destination;
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BACKGROUND);
        root.setFitsSystemWindows(true);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(20), dp(12), dp(20), dp(12));
        header.setBackgroundColor(Color.WHITE);
        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.smartuni_logo);
        logo.setContentDescription("Isotipo SMART UNI: birrete");
        header.addView(logo, new LinearLayout.LayoutParams(dp(62), dp(58)));
        LinearLayout branding = new LinearLayout(this);
        branding.setOrientation(LinearLayout.VERTICAL);
        branding.addView(text("SMART UNI", 22, PRIMARY, true));
        branding.addView(text("Tu espacio universitario", 13, MUTED, false));
        header.addView(branding);
        root.addView(header);

        HorizontalScrollView navScroll = new HorizontalScrollView(this);
        navScroll.setFillViewport(false);
        navScroll.setHorizontalScrollBarEnabled(false);
        LinearLayout nav = new LinearLayout(this);
        nav.setPadding(dp(10), dp(8), dp(10), dp(8));
        for (String name : new String[] {"Inicio", "Apuntes", "Tareas", "Calendario", "Materiales", "Perfil"}) {
            TextView tab = text(name, 15, name.equals(destination) ? Color.WHITE : TEXT, name.equals(destination));
            tab.setPadding(dp(14), dp(10), dp(14), dp(10));
            tab.setBackground(rounded(name.equals(destination) ? PRIMARY : Color.WHITE));
            tab.setContentDescription("Abrir sección " + name);
            tab.setOnClickListener(v -> showScreen(name));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-2, -2);
            lp.setMargins(dp(4), 0, dp(4), 0);
            nav.addView(tab, lp);
        }
        navScroll.addView(nav);
        root.addView(navScroll);

        ScrollView scroller = new ScrollView(this);
        scroller.setFillViewport(true);
        LinearLayout center = new LinearLayout(this);
        center.setGravity(Gravity.TOP | Gravity.CENTER_HORIZONTAL);
        center.setPadding(dp(16), dp(20), dp(16), dp(24));
        mainContent = new LinearLayout(this);
        mainContent.setOrientation(LinearLayout.VERTICAL);
        mainContent.setPadding(dp(20), dp(20), dp(20), dp(20));
        mainContent.setBackground(rounded(Color.WHITE));
        LinearLayout.LayoutParams card = new LinearLayout.LayoutParams(-1, -2);
        card.width = Math.min(getResources().getDisplayMetrics().widthPixels - dp(32), dp(720));
        center.addView(mainContent, card);
        scroller.addView(center);
        root.addView(scroller, new LinearLayout.LayoutParams(-1, 0, 1f));
        setContentView(root);

        mainContent.addView(text(destination, 24, TEXT, true));
        addSpacing(mainContent, 12);
        if ("Apuntes".equals(destination)) {
            showNotes();
        } else if ("Inicio".equals(destination)) {
            showHome();
        } else if ("Perfil".equals(destination)) {
            showProfile();
        } else if ("Tareas".equals(destination)) {
            showTasks();
        } else if ("Calendario".equals(destination)) {
            showCalendar();
        } else if ("Materiales".equals(destination)) {
            showMaterials();
        }
    }

    private void showHome() {
        mainContent.addView(text("Modo local protegido", 18, CTA, true));
        addSpacing(mainContent, 10);
        mainContent.addView(text("Apuntes, tareas, calendario y materiales locales cifrados con Rust. Sin inicio de sesión ni sincronización habilitados.", 16, TEXT, false));
        addSpacing(mainContent, 18);
        mainContent.addView(button("Abrir mis apuntes", () -> showScreen("Apuntes")));
        addSpacing(mainContent, 18);
        try {
            int version = NativeBridge.abiVersion();
            boolean valid = NativeBridge.selfTest();
            mainContent.addView(text(valid && version == 1 ? "Núcleo Rust/JNI: autoprueba correcta (ABI 1)" :
                    "Núcleo nativo: verificación fallida", 14, valid ? CTA : Color.RED, false));
        } catch (LinkageError error) {
            mainContent.addView(text("Núcleo nativo no disponible: se impide guardar contenido.", 14, Color.RED, false));
        }
    }

    private EditText field(String hint, boolean multiline) {
        EditText edit = new EditText(this);
        edit.setTextSize(16);
        edit.setHint(hint);
        edit.setSingleLine(!multiline);
        edit.setInputType(multiline
                ? InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE
                : InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        if (multiline) {
            edit.setMinLines(3);
            edit.setGravity(Gravity.TOP | Gravity.START);
        }
        edit.setContentDescription(hint);
        return edit;
    }

    private void showVaultError(String message) {
        mainContent.addView(text("Bóveda inaccesible: " + message
                + ". No se crearán datos en claro ni se sobrescribirá el contenido.", 15,
                Color.RED, false));
    }

    private void action(String section, VaultAction operation) {
        try {
            operation.run();
            showScreen(section);
        } catch (Exception | LinkageError error) {
            new AlertDialog.Builder(this).setTitle("Operación no realizada")
                    .setMessage("La bóveda cifrada no pudo guardar el cambio. No se utilizó almacenamiento sin protección.")
                    .setPositiveButton("Aceptar", null).show();
        }
    }

    private interface VaultAction {
        void run() throws Exception;
    }

    private void askAdd(String section, String category, boolean detail, boolean date) {
        LinearLayout form = new LinearLayout(this);
        form.setPadding(dp(20), dp(12), dp(20), dp(8));
        form.setOrientation(LinearLayout.VERTICAL);
        EditText title = field("Título", false);
        form.addView(title);
        EditText description = null;
        if (detail) {
            description = field("Contenido del apunte", true);
            form.addView(description);
        }
        final EditText contents = description;
        EditText day = null;
        if (date) {
            day = field("Fecha AAAA-MM-DD", false);
            day.setFocusable(false);
            day.setOnClickListener(v -> {
                Calendar current = Calendar.getInstance();
                new DatePickerDialog(this, (picker, year, month, d) ->
                        ((EditText)v).setText(String.format(java.util.Locale.ROOT,
                                "%04d-%02d-%02d", year, month + 1, d)),
                        current.get(Calendar.YEAR), current.get(Calendar.MONTH),
                        current.get(Calendar.DAY_OF_MONTH)).show();
            });
            day.setContentDescription("Elegir fecha en calendario");
            form.addView(day);
        }
        final EditText dateField = day;
        new AlertDialog.Builder(this).setTitle("Nuevo " + section.toLowerCase(java.util.Locale.ROOT))
                .setView(form)
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Guardar", (dialog, which) -> action(section,
                    () -> new LocalVault(this).add(category, title.getText().toString(),
                        contents == null ? "" : contents.getText().toString(),
                        dateField == null ? "" : dateField.getText().toString()))).show();
    }

    private void askDelete(String section, String category, String id) {
        new AlertDialog.Builder(this).setTitle("Eliminar registro")
                .setMessage("La eliminación será local. No existe aún una copia sincronizada.")
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Eliminar", (dialog, which) -> action(section,
                        () -> new LocalVault(this).delete(category, id))).show();
    }

    private void renderRows(String section, String category) {
        try {
            JSONArray rows = new LocalVault(this).list(category);
            if (rows.length() == 0) {
                mainContent.addView(text("Sin registros en este dispositivo.", 15, MUTED, false));
                return;
            }
            for (int i = rows.length() - 1; i >= 0; i--) {
                JSONObject item = rows.getJSONObject(i);
                String id = item.getString("id");
                String title = item.getString("title");
                addSpacing(mainContent, 12);
                mainContent.addView(text(title, 17, TEXT, true));
                if (LocalVault.NOTES.equals(category)) {
                    String body = item.optString("text");
                    mainContent.addView(text(body.length() > 180
                            ? body.substring(0, 180) + "…"
                            : body, 14, MUTED, false));
                    mainContent.addView(button("Editar " + title, () ->
                            askEditNote(id, title, body)));
                } else if (LocalVault.EVENTS.equals(category)) {
                    mainContent.addView(text(item.optString("date"), 15, MUTED, false));
                } else if (LocalVault.TASKS.equals(category)) {
                    boolean done = item.optBoolean("done");
                    mainContent.addView(button(done ? "Marcar pendiente" : "Completar tarea",
                            () -> action(section, () -> new LocalVault(this).toggleTask(id))));
                }
                mainContent.addView(button("Eliminar " + title,
                        () -> askDelete(section, category, id)));
            }
        } catch (Exception | LinkageError error) {
            showVaultError("fallo de autenticación, clave o lectura");
        }
    }

    private void askEditNote(String id, String oldTitle, String oldBody) {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(dp(16), dp(8), dp(16), dp(8));
        EditText title = field("Título", false);
        title.setText(oldTitle);
        form.addView(title);
        EditText body = field("Contenido", true);
        body.setText(oldBody);
        form.addView(body);
        new AlertDialog.Builder(this).setTitle("Editar apunte")
            .setView(form)
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Guardar", (dialog, which) ->
                action("Apuntes", () -> new LocalVault(this)
                    .updateNote(id, title.getText().toString(), body.getText().toString())))
            .show();
    }

    private void showNotes() {
        mainContent.addView(text("Apuntes privados de este dispositivo", 15, MUTED, false));
        addSpacing(mainContent, 12);
        mainContent.addView(button("Nuevo apunte", () ->
                askAdd("Apuntes", LocalVault.NOTES, true, false)));
        renderRows("Apuntes", LocalVault.NOTES);
    }

    private void showTasks() {
        mainContent.addView(text("Lista de tareas offline cifrada. Aún no se sincroniza.", 15, MUTED, false));
        addSpacing(mainContent, 12);
        mainContent.addView(button("Nueva tarea", () ->
                askAdd("Tareas", LocalVault.TASKS, false, false)));
        renderRows("Tareas", LocalVault.TASKS);
    }

    private void showCalendar() {
        mainContent.addView(text("Eventos locales sin integración con calendario externo.", 15, MUTED, false));
        addSpacing(mainContent, 12);
        mainContent.addView(button("Nuevo evento", () ->
                askAdd("Calendario", LocalVault.EVENTS, false, true)));
        renderRows("Calendario", LocalVault.EVENTS);
    }

    private void showMaterials() {
        mainContent.addView(text("Archivos cifrados en almacenamiento privado, sin subirlos a la nube.", 15, MUTED, false));
        addSpacing(mainContent, 12);
        mainContent.addView(button("Importar material (máximo 8 MiB)", () -> {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.setType("*/*");
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(intent, 81);
        }));
        try {
            JSONArray rows = new LocalVault(this).list(LocalVault.MATERIALS);
            if (rows.length() == 0) {
                mainContent.addView(text("Todavía no hay materiales importados.", 14, MUTED, false));
            }
            for (int i = rows.length() - 1; i >= 0; i--) {
                JSONObject item = rows.getJSONObject(i);
                String id = item.getString("id");
                String filename = item.getString("title");
                String fileId = item.optString("text");
                addSpacing(mainContent, 10);
                mainContent.addView(text(filename, 16, TEXT, true));
                mainContent.addView(text(item.optString("date") + " bytes cifrados", 13, MUTED, false));
                mainContent.addView(button("Vista previa de texto", () -> previewMaterial(fileId, filename)));
                mainContent.addView(button("Eliminar material", () ->
                        new AlertDialog.Builder(this).setTitle("Eliminar material")
                        .setMessage("Se eliminará la referencia y el archivo cifrado local.")
                        .setNegativeButton("Cancelar", null)
                        .setPositiveButton("Eliminar", (dialog, which) ->
                            action("Materiales", () ->
                                new MaterialVault(this).deleteMaterial(fileId, id))).show()));
            }
        } catch (Exception | LinkageError error) {
            showVaultError("no se pueden leer los materiales");
        }
    }

    private void previewMaterial(String fileId, String filename) {
        String lower = filename.toLowerCase(java.util.Locale.ROOT);
        if (!(lower.endsWith(".txt") || lower.endsWith(".md") || lower.endsWith(".csv"))) {
            new AlertDialog.Builder(this).setTitle("Vista previa no disponible")
                    .setMessage("No se abrirán PDF, Office ni imágenes con aplicaciones externas sin una política de exportación segura.")
                    .setPositiveButton("Aceptar", null).show();
            return;
        }
        io.execute(() -> {
            String message;
            try {
                byte[] data = new MaterialVault(this).readMaterial(fileId);
                try {
                    message = new String(data, StandardCharsets.UTF_8);
                } finally {
                    Arrays.fill(data, (byte) 0);
                }
            } catch (Exception | LinkageError e) {
                message = "No se pudo autenticar o leer este material.";
            }
            final String preview = message;
            runOnUiThread(() -> {
                if (!isFinishing() && !isDestroyed()) {
                    ScrollView scroll = new ScrollView(this);
                    TextView body = text(preview, 14, TEXT, false);
                    body.setPadding(dp(18), dp(12), dp(18), dp(12));
                    scroll.addView(body);
                    new AlertDialog.Builder(this).setTitle(filename).setView(scroll)
                            .setPositiveButton("Cerrar", null).show();
                }
            });
        });
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != 81 || resultCode != RESULT_OK || data == null ||
                data.getData() == null) return;
        final Uri uri = data.getData();
        io.execute(() -> {
            boolean saved = false;
            try {
                new MaterialVault(this).importDocument(uri);
                saved = true;
            } catch (Exception | LinkageError ignored) {
                // No registrar URI, ruta o contenido sensible.
            }
            final boolean imported = saved;
            runOnUiThread(() -> {
                if (!isFinishing() && !isDestroyed()) {
                    showScreen("Materiales");
                    new AlertDialog.Builder(this)
                        .setTitle(imported ? "Material cifrado" : "No se pudo importar")
                        .setMessage(imported
                            ? "Material guardado localmente con Rust y Android Keystore."
                            : "Archivo inaccesible, tipo no admitido, demasiado grande o error de cifrado. No se guardó contenido en claro.")
                        .setPositiveButton("Aceptar", null).show();
                }
            });
        });
    }

    private void showProfile() {
        mainContent.addView(text("Sesión: desconectada", 17, MUTED, true));
        addSpacing(mainContent, 8);
        mainContent.addView(text("OIDC/PKCE y enrolamiento seguro de dispositivos son requisitos pendientes. No se aceptan credenciales locales falsas.", 14, TEXT, false));
        addSpacing(mainContent, 18);
        mainContent.addView(text("Diagnóstico HTTPS (solo /healthz; no envía datos privados)", 16, TEXT, true));
        EditText origin = new EditText(this);
        origin.setHint("https://servidor.example");
        origin.setSingleLine(true);
        origin.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_URI);
        origin.setContentDescription("Origen HTTPS de diagnóstico");
        mainContent.addView(origin);
        TextView result = text("Sin comprobar", 14, MUTED, false);
        mainContent.addView(button("Comprobar conectividad", () -> {
            String value = origin.getText().toString().trim();
            result.setText("Comprobando mediante JNI...");
            io.execute(() -> {
                int status = NativeBridge.checkHealth(value);
                runOnUiThread(() -> result.setText(status == 200 ? "Servidor HTTPS responde 200" :
                        status > 0 ? "Respuesta HTTP " + status + " (no confirma autenticación)" :
                                "No disponible / URL inválida / fallo de TLS"));
            });
        }));
        addSpacing(mainContent, 12);
        mainContent.addView(result);
    }

    @Override protected void onDestroy() {
        io.shutdownNow();
        super.onDestroy();
    }
}
