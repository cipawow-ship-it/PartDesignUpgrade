# -*- coding: utf-8 -*-
"""Lightweight i18n for PartDesignUpgrade.

Strings are keyed by their English source text; ``tr()`` returns the
translation for the language configured in FreeCAD (falls back to English for
untranslated strings). Enum values stored in Part property enumerations keep
their canonical English values in itemData, only the *display* text is
translated.
"""

import FreeCAD

_SUPPORTED = ("en", "it", "fr", "de", "es", "pt", "pl", "ru", "zh")

_KNOWN = {
    "en": "en", "english": "en",
    "it": "it", "italian": "it", "italiano": "it",
    "fr": "fr", "french": "fr", "francais": "fr", "français": "fr",
    "de": "de", "german": "de", "deutsch": "de",
    "es": "es", "spanish": "es", "espanol": "es", "español": "es",
    "pt": "pt", "portuguese": "pt", "portugues": "pt", "português": "pt",
    "pl": "pl", "polish": "pl", "polski": "pl",
    "ru": "ru", "russian": "ru", "русский": "ru",
    "zh": "zh", "chinese": "zh", "zhongwen": "zh",
    "简体中文": "zh", "繁体中文": "zh", "中文": "zh",
}


def _normalize_words(raw):
    s = "".join(c if c.isalnum() else " " for c in str(raw).lower())
    return " ".join(s.split())


def _code_from_locale(raw):
    words = _normalize_words(raw)
    if not words:
        return None
    first = words.split(" ")[0]
    compact = words.replace(" ", "")
    if words in _KNOWN:
        return _KNOWN[words]
    if first in _KNOWN:
        return _KNOWN[first]
    if compact[:2] in _SUPPORTED:
        return compact[:2]
    return None


def current_lang():
    try:
        import FreeCADGui
    except Exception:
        FreeCADGui = None
    if FreeCADGui is not None and hasattr(FreeCADGui, "getLocale"):
        try:
            code = _code_from_locale(FreeCADGui.getLocale())
            if code in _SUPPORTED:
                return code
        except Exception:
            pass
    try:
        raw = FreeCAD.ParamGet(
            "User parameter:BaseApp/Preferences/General"
        ).GetString("Language", "") or ""
        code = _code_from_locale(raw)
        if code in _SUPPORTED:
            return code
    except Exception:
        pass
    return "en"


_TRANSLATIONS = {
    "it": {
        'Rectangle': 'Rettangolo',
        'Triangle': 'Triangolo',
        'Rotation angle (Â°):': 'Angolo di rotazione (Â°):',
        'The rib is a plate closing the corner between the planar\nface and the cylinder, like between two non-parallel\nsurfaces.  Rectangle or Triangle profile.  Copies places N\nplates rotated around the cylinder axis.  The inner edge\nsinks into the cylinder until both its corners touch the\ncylinder surface.  Angle rotates the ribs around the axis\nto position them where wanted.': "La nervatura è una piastra che chiude l'angolo tra la faccia piana e il cilindro,\ncome tra due superfici non parallele.  Profilo Rettangolo o Triangolo.  Le copie\nposizionano N piastre ruotate attorno all'asse del cilindro.  Il bordo interno si\ninfossa nel cilindro finché entrambi i suoi angoli toccano la superficie del cilindro.\nL’angolo ruota le nervature attorno all’asse per posizionarle dove si vuole.",

        'Full face length': 'Lunghezza su tutta la faccia',
        'Create Rib Between Faces': 'Crea Nervatura tra Facce',
        'Create a rib between two selected faces': 'Crea una nervatura tra due facce selezionate',
        'Length on face 1:': 'Lunghezza su faccia 1:',
        'Length on face 2:': 'Lunghezza su faccia 2:',
        'Offset:': 'Offset:',
        'Copies:': 'Copie:',
        'Select exactly two faces.': 'Seleziona esattamente due facce.',
        'The faces are not usable: select two angled planar faces, or a planar face and a cylinder.': 'Le facce non sono utilizzabili: seleziona due facce piane, oppure una faccia piana e un cilindro.',
        'The rib is a plate closing the angle between two non-parallel\nplanar faces.  Rectangle or Triangle profile.  L1 and L2 are\nthe contact lengths on faces 1 and 2, measured from the\ncorner edge.  Offset slides the plate along the corner edge.\nCopies places N plates spaced with the Spacing distance.': "La nervatura è una piastra che chiude l'angolo tra due facce\nnon parallele.  Profilo Rettangolo o Triangolo.  L1 e L2 sono le\nlunghezze di contatto sulle facce 1 e 2, misurate dallo spigolo.\nL'offset fa scorrere la piastra lungo lo spigolo.\nLe copie posizionano N piastre distanziate della distanza Spacing.",
        'Create a stiffening rib between two selected faces: an angled corner, or a flat face and a cylinder': 'Crea una nervatura di irrigidimento tra due facce selezionate: un angolo, oppure un piano e un cilindro',
        'Spacing:': 'Distanza:',

        'Rib between faces: {}': 'Nervatura tra facce: {}',
        "Additive rib between faces added to '{}'.": "Nervatura additiva tra facce aggiunta a '{}'.",
        'Rib between faces created.': 'Nervatura tra facce creata.',
        'Length on face 1 must be positive': 'La lunghezza su faccia 1 deve essere positiva',
        'Length on face 2 must be positive': 'La lunghezza su faccia 2 deve essere positiva',
        'The two faces share the same centre.': 'Le due facce hanno lo stesso centro.',
        'The gap between the two faces is too small.': 'La distanza tra le due facce è troppo piccola.',
        'The cylindrical face could not be read.': 'Impossibile leggere la faccia cilindrica.',
        'The rib is a vertical plate from the planar face up against the cylinder.  Copies places N ribs rotated around the cylinder axis.  Offset slides the plate along the axis.': "La nervatura è una piastra verticale dal piano fino al cilindro.  Copie posiziona N nervature ruotate attorno all'asse del cilindro.  L'offset fa scorrere la piastra lungo l'asse.",
        "Create Rib": "Crea Nervatura",
        "Create a stiffening rib from a sketch profile, extruded perpendicular to the sketch plane": "Crea una nervatura di irrigidimento da un profilo dello sketch, estruso perpendicolarmente al piano dello sketch",
        "Create a rib from a selected sketch": "Crea una nervatura da uno sketch selezionato",
        "Subtractive Rib": "Nervatura Sottrattiva",
        "Remove a rib from the body: extrude a sketch profile perpendicular to the plane and subtract it": "Rimuove una nervatura dal corpo: estrude un profilo dello sketch perpendicolarmente al piano e lo sottrae",
        "Subtract a rib-shaped volume from the body": "Sottrae un volume a forma di nervatura dal corpo",
        "Thickness:": "Spessore:",
        "Midplane:": "Piano medio:",
        "Reversed:": "Inverti:",
        "Invert leg 1:": "Inverti cateto 1:",
        "Invert leg 2:": "Inverti cateto 2:",
        "Thickness is applied perpendicular to the sketch plane.\nMidplane: thickness extends equally on both sides.\nReversed: flip the normal direction.": "Lo spessore è applicato perpendicolarmente al piano dello sketch.\nPiano medio: lo spessore si estende ugualmente su entrambi i lati.\nInverti: capovolge la direzione della normale.",
        "Select a sketch as the rib profile.": "Seleziona uno sketch come profilo della nervatura.",
        "Additive rib added to '{}'.": "Nervatura additiva aggiunta a '{}'.",
        "Subtractive rib removed from '{}'.": "Nervatura sottrattiva rimossa da '{}'.",
        "Subtractive rib needs a PartDesign body to cut.": "La nervatura sottrattiva richiede un corpo PartDesign da tagliare.",
        "Rib created.": "Nervatura creata.",
        "Thickness must be positive": "Lo spessore deve essere positivo",
        "The profile is degenerate: it has no area to extrude. Draw a closed profile or an open profile with more than one edge.": "Il profilo è degenere: non ha area da estrudere. Disegna un profilo chiuso o un profilo aperto con più di uno spigolo.",
        "The profile is degenerate: it has no area to extrude. A single straight line cannot form a rib; use at least two connected edges, an arc, or a closed profile.": "Il profilo è degenere: non ha area da estrudere. Una singola linea retta non può formare una nervatura; usa almeno due spigoli connessi, un arco o un profilo chiuso.",
        "Rib: {}": "Nervatura: {}",
        "Create Pipe": "Crea Tubo",
        "Create a parametric pipe sweeping a profile along a sketch or edge path":
            "Crea un tubo parametrico che trasla un profilo lungo uno sketch o un percorso di spigoli",
        "Create a pipe along a selected sketch or edges":
            "Crea un tubo lungo uno sketch o spigoli selezionati",
        "Subtractive Pipe": "Tubo Sottrattivo",
        "Remove a pipe from the body: sweep a profile along a path and subtract it":
            "Rimuove un tubo dal corpo: trasla un profilo lungo un percorso e lo sottrae",
        "Subtract a pipe-shaped volume from the selected body":
            "Sottrae un volume a forma di tubo dal corpo selezionato",
        "Assembly Cut": "Taglio Assembly",
        "Cut several PartDesign bodies at once using one sketch":
            "Taglia più corpi PartDesign contemporaneamente usando un solo sketch",
        "Cut multiple bodies with a single sketch":
            "Taglia più corpi con un singolo sketch",
        "Weight / Volume": "Peso / Volume",
        "Compute the volume and the weight of a body with a material density selector":
            "Calcola il volume e il peso di un corpo con un selettore di densità del materiale",
        "Show volume and mass of the selected body":
            "Mostra volume e massa del corpo selezionato",
        "Part Design Upgrade": "Part Design Upgrade",
        "PartDesign helpers: pipe, assembly cut and weight/volume":
            "Utilità PartDesign: tubo, taglio assembly e peso/volume",
        "Profile shape:": "Forma profilo:",
        "Circle": "Cerchio",
        "Square": "Quadrato",
        "Triangle": "Triangolo",
        "Pentagon": "Pentagono",
        "Hexagon": "Esagono",
        "Octagon": "Ottagono",
        "Side length:": "Lato:",
        "Radius:": "Raggio:",
        "Wall thickness:": "Spessore parete:",
        "Rotation:": "Rotazione:",
        "Corner transition:": "Transizione angolo:",
        "Profile offset": "Offset profilo",
        "Center": "Centra",
        "Rotation turns the cross-section around the pipe axis.\nOffset (0 = centered on the path): X moves the profile sideways,\nY moves it up/down (both also negative).\nWall thickness (0 = solid): hollows out the pipe, keeping the\ndimension above as the EXTERNAL size.":
            "La rotazione ruota la sezione attorno all'asse del tubo.\nOffset (0 = centrato sul percorso): X sposta il profilo lateralmente,\nY lo sposta su/giù (anche valori negativi).\nSpessore parete (0 = pieno): svuota il tubo mantenendo la\ndimensione sopra come dimensione ESTERNA.",
        "Preview": "Anteprima",
        "Show final result": "Mostra risultato finale",
        "Show overlapping preview": "Mostra anteprima sovrapposta",
        "Right corner": "Angolo retto",
        "Round corner": "Angolo arrotondato",
        "Transformed": "Trasformata",
        "No active document": "Nessun documento attivo",
        "Select a sketch, or one or more edges of a body, as the pipe path.":
            "Seleziona uno sketch, oppure uno o più spigoli di un corpo, come percorso del tubo.",
        "The selected sketch is empty.": "Lo sketch selezionato è vuoto.",
        "The selected edges do not form a connected path: {}":
            "Gli spigoli selezionati non formano un percorso connesso: {}",
        "Additive pipe added to '{}'.": "Tubo additivo aggiunto a '{}'.",
        "Subtractive pipe removed from '{}'.": "Tubo sottrattivo rimosso da '{}'.",
        "Subtractive pipe needs a PartDesign body to cut.":
            "Il tubo sottrattivo richiede un corpo PartDesign da tagliare.",
        "Pipe created.": "Tubo creato.",
        "Wall thickness too large for the profile: keeping a solid pipe.":
            "Spessore parete troppo grande per il profilo: mantengo un tubo pieno.",
        "Pipe sweep truncated on this path (volume {:.1f}, expected ~{:.1f}). Reduce the profile size or offset, or round the path corners.":
            "Sweep del tubo troncato su questo percorso (volume {:.1f}, previsto ~{:.1f}). Riduci dimensione o offset del profilo, o arrotonda gli angoli del percorso.",
        "Note: corner transition '{}' is not possible at this profile rotation; using '{}' (profile rotation left unchanged).":
            "Nota: la transizione d'angolo '{}' non è possibile con questa rotazione; uso '{}' (rotazione del profilo invariata).",
        "Could not sweep the profile along the path (degenerate result). Try changing the profile size or smoothing the path corners.":
            "Impossibile traslare il profilo lungo il percorso (risultato degenere). Prova a cambiare la dimensione del profilo o ad arrotondare gli angoli del percorso.",
        "Body:": "Corpo:",
        "Object:": "Oggetto:",
        "Volume:": "Volume:",
        "Material:": "Materiale:",
        "Custom density:": "Densità personalizzata:",
        "Mass: {:.3f} g   ({:.6f} kg)": "Massa: {:.3f} g   ({:.6f} kg)",
        "Total ({} parts): {:.3f} g   ({:.3f} cm\u00b3)":
            "Totale ({} parti): {:.3f} g   ({:.3f} cm\u00b3)",
        "Part": "Parte",
        "Material": "Materiale",
        "Mass (g)": "Massa (g)",
        "Each part keeps its own material. 'Total' sums every part\nwith the material assigned to each one. Selecting a body in\nthe 3D view (or clicking a row) selects it here.":
            "Ogni parte mantiene il proprio materiale. 'Totale' somma ogni parte\ncol materiale assegnato a ciascuna. Selezionare un corpo nella\nvista 3D (o fare clic su una riga) lo seleziona qui.",
        "Select a PartDesign body or a shape with volume first.":
            "Seleziona prima un corpo PartDesign o una forma con volume.",
        "Sketch: ": "Sketch: ",
        "Select bodies to cut (reorder with arrows):":
            "Seleziona i corpi da tagliare (riordinare con le frecce):",
        "Mode:": "Modalità:",
        "Independent sketches (full copy)": "Sketch indipendenti (copia completa)",
        "Binder (linked to sketch)": "Binder (collegato allo sketch)",
        "Each body gets an independent copy of the sketch.":
            "Ogni corpo riceve una copia indipendente dello sketch.",
        "Each body gets a binder linked to the original sketch.":
            "Ogni corpo riceve un binder collegato allo sketch originale.",
        "Cut Bodies": "Taglia Corpi",
        "Cancel": "Annulla",
        "Select All": "Seleziona Tutti",
        "Deselect All": "Deseleziona Tutti",
        "No active document.": "Nessun documento attivo.",
        "Select a Sketch first, then run this command.":
            "Seleziona prima uno Sketch, poi avvia questo comando.",
        "No PartDesign::Body found in document.":
            "Nessun PartDesign::Body trovato nel documento.",
        "Error creating profile for ": "Errore nella creazione del profilo per ",
        "Export CSV…": "Esporta CSV…",
        "Save the part list with material and mass as a CSV file.":
            "Salva l'elenco dei componenti con materiale e massa in un file CSV.",
        "Export BOM as CSV": "Esporta BOM come CSV",
        "CSV files (*.csv)": "File CSV (*.csv)",
        "Volume (cm\u00b3)": "Volume (cm\u00b3)",
        "Density (kg/m\u00b3)": "Densità (kg/m\u00b3)",
        "Total": "Totale",
        "Unable to write file:\n{}": "Impossibile scrivere il file:\n{}",
        "BOM exported to:\n{}": "BOM esportata in:\n{}",
    },
    "fr": {
        'Rectangle': 'Rectangle',
        'Triangle': 'Triangle',
        'Rotation angle (Â°):': 'Angle de rotation (Â°) :',
        'The rib is a plate closing the corner between the planar\nface and the cylinder, like between two non-parallel\nsurfaces.  Rectangle or Triangle profile.  Copies places N\nplates rotated around the cylinder axis.  The inner edge\nsinks into the cylinder until both its corners touch the\ncylinder surface.  Angle rotates the ribs around the axis\nto position them where wanted.': "La nervure est une plaque fermant l'angle entre le plan et le cylindre,\ncomme entre deux surfaces non parallèles.  Profil Rectangle ou Triangle.\nLes copies placent N plaques autour de l'axe du cylindre.  Le bord interne\ns'enfonce dans le cylindre jusqu'à ce que ses deux angles touchent la surface.\nL’angle fait pivoter les nervures autour de l’axe pour les positionner où vous le souhaitez.",

        'Full face length': 'Longueur sur toute la face',
        'Create Rib Between Faces': 'Créer une nervure entre faces',
        'Create a rib between two selected faces': 'Créer une nervure entre deux faces sélectionnées',
        'Length on face 1:': 'Longueur sur la face 1 :',
        'Length on face 2:': 'Longueur sur la face 2 :',
        'Offset:': 'Décalage :',
        'Copies:': 'Copies :',
        'Select exactly two faces.': 'Sélectionnez exactement deux faces.',
        'The faces are not usable: select two angled planar faces, or a planar face and a cylinder.': 'Les faces ne sont pas utilisables : sélectionnez deux faces planes, ou une face plane et un cylindre.',
        'The rib is a plate closing the angle between two non-parallel\nplanar faces.  Rectangle or Triangle profile.  L1 and L2 are\nthe contact lengths on faces 1 and 2, measured from the\ncorner edge.  Offset slides the plate along the corner edge.\nCopies places N plates spaced with the Spacing distance.': "La nervure est une plaque fermant l'angle entre deux faces non parallèles.\nProfil Rectangle ou Triangle.  L1 et L2 sont les longueurs de contact sur\nles faces 1 et 2, mesurées depuis le bord.  Le décalage fait glisser la\nplaque le long du bord.\nLes copies placent N plaques espacées de la distance Espacement.",
        'Create a stiffening rib between two selected faces: an angled corner, or a flat face and a cylinder': 'Crea una nervatura di irrigidimento tra due facce selezionate: un angolo, oppure un piano e un cilindro',
        'Spacing:': 'Espacement :',

        'Rib between faces: {}': 'Nervure entre faces : {}',
        "Additive rib between faces added to '{}'.": "Nervure additive entre faces ajoutée à '{}'.",
        'Rib between faces created.': 'Nervure entre faces créée.',
        'Length on face 1 must be positive': 'La longueur sur la face 1 doit être positive',
        'Length on face 2 must be positive': 'La longueur sur la face 2 doit être positive',
        'The two faces share the same centre.': 'Les deux faces partagent le même centre.',
        'The gap between the two faces is too small.': "L'espace entre les deux faces est trop petit.",
        'The cylindrical face could not be read.': "La face cylindrique n'a pas pu être lue.",
        'The rib is a vertical plate from the planar face up against the cylinder.  Copies places N ribs rotated around the cylinder axis.  Offset slides the plate along the axis.': "La nervure est une plaque verticale allant du plan au cylindre.  Copies place N nervures tournées autour de l'axe du cylindre.  Le décalage fait glisser la plaque le long de l'axe.",
        "Create Rib": "Créer une nervure",
        "Create a stiffening rib from a sketch profile, extruded perpendicular to the sketch plane": "Créer une nervure de rigidification à partir d'un profil d'esquisse, extrudé perpendiculairement au plan de l'esquisse",
        "Create a rib from a selected sketch": "Créer une nervure à partir d'une esquisse sélectionnée",
        "Subtractive Rib": "Nervure soustractive",
        "Remove a rib from the body: extrude a sketch profile perpendicular to the plane and subtract it": "Retirer une nervure du corps : extruder un profil d'esquisse perpendiculairement au plan puis le soustraire",
        "Subtract a rib-shaped volume from the body": "Soustraire un volume en forme de nervure du corps",
        "Thickness:": "Épaisseur :",
        "Midplane:": "Plan médian :",
        "Reversed:": "Inversé :",
        "Invert leg 1:": "Inverser le côté 1 :",
        "Invert leg 2:": "Inverser le côté 2 :",
        "Thickness is applied perpendicular to the sketch plane.\nMidplane: thickness extends equally on both sides.\nReversed: flip the normal direction.": "L'épaisseur est appliquée perpendiculairement au plan de l'esquisse.\nPlan médian : l'épaisseur s'étend également des deux côtés.\nInversé : inverse la direction de la normale.",
        "Select a sketch as the rib profile.": "Sélectionnez une esquisse comme profil de nervure.",
        "Additive rib added to '{}'.": "Nervure additive ajoutée à '{}'.",
        "Subtractive rib removed from '{}'.": "Nervure soustractive retirée de '{}'.",
        "Subtractive rib needs a PartDesign body to cut.": "La nervure soustractive nécessite un corps PartDesign à découper.",
        "Rib created.": "Nervure créée.",
        "Thickness must be positive": "L'épaisseur doit être positive",
        "The profile is degenerate: it has no area to extrude. Draw a closed profile or an open profile with more than one edge.": "Le profil est dégénéré : pas de surface à extruder. Dessinez un profil fermé ou un profil ouvert avec plus d'une arête.",
        "The profile is degenerate: it has no area to extrude. A single straight line cannot form a rib; use at least two connected edges, an arc, or a closed profile.": "Le profil est dégénéré : pas de surface à extruder. Une simple ligne droite ne peut pas former une nervure ; utilisez au moins deux arêtes connectées, un arc ou un profil fermé.",
        "Rib: {}": "Nervure : {}",
        "Create Pipe": "Créer un tuyau",
        "Create a parametric pipe sweeping a profile along a sketch or edge path":
            "Créer un tuyau paramétrique balayant un profil le long d'une esquisse ou d'un chemin d'arêtes",
        "Create a pipe along a selected sketch or edges":
            "Créer un tuyau le long d'une esquisse ou d'arêtes sélectionnées",
        "Subtractive Pipe": "Tuyau soustractif",
        "Remove a pipe from the body: sweep a profile along a path and subtract it":
            "Retirer un tuyau du corps : balayer un profil le long d'un chemin puis le soustraire",
        "Subtract a pipe-shaped volume from the selected body":
            "Soustraire un volume en forme de tuyau du corps sélectionné",
        "Assembly Cut": "Découpe d'assemblage",
        "Cut several PartDesign bodies at once using one sketch":
            "Découper plusieurs corps PartDesign à la fois avec une seule esquisse",
        "Cut multiple bodies with a single sketch":
            "Découper plusieurs corps avec une seule esquisse",
        "Weight / Volume": "Poids / Volume",
        "Compute the volume and the weight of a body with a material density selector":
            "Calculer le volume et le poids d'un corps avec un sélecteur de densité de matériau",
        "Show volume and mass of the selected body":
            "Afficher le volume et la masse du corps sélectionné",
        "Part Design Upgrade": "Part Design Upgrade",
        "PartDesign helpers: pipe, assembly cut and weight/volume":
            "Utilitaires PartDesign : tuyau, découpe d'assemblage et poids/volume",
        "Profile shape:": "Forme du profil :",
        "Circle": "Cercle",
        "Square": "Carré",
        "Triangle": "Triangle",
        "Pentagon": "Pentagone",
        "Hexagon": "Hexagone",
        "Octagon": "Octogone",
        "Side length:": "Longueur de côté :",
        "Radius:": "Rayon :",
        "Wall thickness:": "Épaisseur de paroi :",
        "Rotation:": "Rotation :",
        "Corner transition:": "Transition d'angle :",
        "Profile offset": "Décalage du profil",
        "Center": "Centrer",
        "Rotation turns the cross-section around the pipe axis.\nOffset (0 = centered on the path): X moves the profile sideways,\nY moves it up/down (both also negative).\nWall thickness (0 = solid): hollows out the pipe, keeping the\ndimension above as the EXTERNAL size.":
            "La rotation fait pivoter la section autour de l'axe du tuyau.\nDécalage (0 = centré sur le chemin) : X déplace le profil latéralement,\nY de haut en bas (les valeurs négatives aussi).\nÉpaisseur de paroi (0 = plein) : creuse le tuyau en conservant la\ndimension ci-dessus comme taille EXTERNE.",
        "Preview": "Aperçu",
        "Show final result": "Afficher le résultat final",
        "Show overlapping preview": "Afficher l'aperçu en chevauchement",
        "Right corner": "Angle droit",
        "Round corner": "Angle arrondi",
        "Transformed": "Transformée",
        "No active document": "Aucun document actif",
        "Select a sketch, or one or more edges of a body, as the pipe path.":
            "Sélectionnez une esquisse, ou une ou plusieurs arêtes d'un corps, comme chemin du tuyau.",
        "The selected sketch is empty.": "L'esquisse sélectionnée est vide.",
        "The selected edges do not form a connected path: {}":
            "Les arêtes sélectionnées ne forment pas un chemin connecté : {}",
        "Additive pipe added to '{}'.": "Tuyau additif ajouté à '{}'.",
        "Subtractive pipe removed from '{}'.": "Tuyau soustractif retiré de '{}'.",
        "Subtractive pipe needs a PartDesign body to cut.":
            "Le tuyau soustractif nécessite un corps PartDesign à découper.",
        "Pipe created.": "Tuyau créé.",
        "Wall thickness too large for the profile: keeping a solid pipe.":
            "Épaisseur de paroi trop grande pour le profil : conservation d'un tuyau plein.",
        "Pipe sweep truncated on this path (volume {:.1f}, expected ~{:.1f}). Reduce the profile size or offset, or round the path corners.":
            "Balayage du tuyau tronqué sur ce chemin (volume {:.1f}, attendu ~{:.1f}). Réduisez la taille ou le décalage du profil, ou arrondissez les angles du chemin.",
        "Note: corner transition '{}' is not possible at this profile rotation; using '{}' (profile rotation left unchanged).":
            "Note : la transition d'angle '{}' est impossible avec cette rotation ; utilisation de '{}' (rotation du profil inchangée).",
        "Could not sweep the profile along the path (degenerate result). Try changing the profile size or smoothing the path corners.":
            "Impossible de balayer le profil le long du chemin (résultat dégénéré). Changez la taille du profil ou arrondissez les angles du chemin.",
        "Body:": "Corps :",
        "Object:": "Objet :",
        "Volume:": "Volume :",
        "Material:": "Matériau :",
        "Custom density:": "Densité personnalisée :",
        "Mass: {:.3f} g   ({:.6f} kg)": "Masse : {:.3f} g   ({:.6f} kg)",
        "Total ({} parts): {:.3f} g   ({:.3f} cm\u00b3)":
            "Total ({} pièces) : {:.3f} g   ({:.3f} cm\u00b3)",
        "Part": "Pièce",
        "Material": "Matériau",
        "Mass (g)": "Masse (g)",
        "Each part keeps its own material. 'Total' sums every part\nwith the material assigned to each one. Selecting a body in\nthe 3D view (or clicking a row) selects it here.":
            "Chaque pièce garde son propre matériau. 'Total' additionne chaque pièce\navec le matériau qui lui est assigné. Sélectionner un corps dans la\nvue 3D (ou cliquer une ligne) le sélectionne ici.",
        "Select a PartDesign body or a shape with volume first.":
            "Sélectionnez d'abord un corps PartDesign ou une forme avec un volume.",
        "Sketch: ": "Esquisse : ",
        "Select bodies to cut (reorder with arrows):":
            "Sélectionnez les corps à découper (réordonner avec les flèches) :",
        "Mode:": "Mode :",
        "Independent sketches (full copy)": "Esquisses indépendantes (copie complète)",
        "Binder (linked to sketch)": "Binder (lié à l'esquisse)",
        "Each body gets an independent copy of the sketch.":
            "Chaque corps reçoit une copie indépendante de l'esquisse.",
        "Each body gets a binder linked to the original sketch.":
            "Chaque corps reçoit un binder lié à l'esquisse originale.",
        "Cut Bodies": "Découper les corps",
        "Cancel": "Annuler",
        "Select All": "Tout sélectionner",
        "Deselect All": "Tout désélectionner",
        "No active document.": "Aucun document actif.",
        "Select a Sketch first, then run this command.":
            "Sélectionnez d'abord une esquisse, puis lancez cette commande.",
        "No PartDesign::Body found in document.":
            "Aucun PartDesign::Body trouvé dans le document.",
        "Error creating profile for ": "Erreur lors de la création du profil pour ",
        "Export CSV…": "Exporter CSV…",
        "Save the part list with material and mass as a CSV file.":
            "Enregistrer la liste des pièces avec matériau et masse dans un fichier CSV.",
        "Export BOM as CSV": "Exporter la nomenclature en CSV",
        "CSV files (*.csv)": "Fichiers CSV (*.csv)",
        "Volume (cm\u00b3)": "Volume (cm\u00b3)",
        "Density (kg/m\u00b3)": "Densité (kg/m\u00b3)",
        "Total": "Total",
        "Unable to write file:\n{}": "Impossible d'écrire le fichier :\n{}",
        "BOM exported to:\n{}": "Nomenclature exportée dans :\n{}",
    },
    "de": {
        'Rectangle': 'Rechteck',
        'Triangle': 'Dreieck',
        'Rotation angle (Â°):': 'Drehwinkel (Â°):',
        'The rib is a plate closing the corner between the planar\nface and the cylinder, like between two non-parallel\nsurfaces.  Rectangle or Triangle profile.  Copies places N\nplates rotated around the cylinder axis.  The inner edge\nsinks into the cylinder until both its corners touch the\ncylinder surface.  Angle rotates the ribs around the axis\nto position them where wanted.': 'Die Rippe ist eine Platte, die die Ecke zwischen der planaren Fläche\nund dem Zylinder schließt, wie zwischen zwei nicht parallelen Flächen.\nProfil Rechteck oder Dreieck.  Kopien platzieren N Platten um die\nZylinderachse.  Die Innenkante dringt in den Zylinder, bis beide Ecken\ndie Zylinderfläche berühren.\nDer Winkel dreht die Rippen um die Achse, um sie beliebig zu positionieren.',

        'Full face length': 'Länge über die ganze Fläche',
        'Create Rib Between Faces': 'Rippe zwischen Flächen erstellen',
        'Create a rib between two selected faces': 'Eine Rippe zwischen zwei ausgewählten Flächen erstellen',
        'Length on face 1:': 'Länge auf Fläche 1:',
        'Length on face 2:': 'Länge auf Fläche 2:',
        'Offset:': 'Versatz:',
        'Copies:': 'Kopien:',
        'Select exactly two faces.': 'Genau zwei Flächen auswählen.',
        'The faces are not usable: select two angled planar faces, or a planar face and a cylinder.': 'Die Flächen sind nicht geeignet: wählen Sie zwei ebene Flächen oder eine ebene Fläche und einen Zylinder.',
        'The rib is a plate closing the angle between two non-parallel\nplanar faces.  Rectangle or Triangle profile.  L1 and L2 are\nthe contact lengths on faces 1 and 2, measured from the\ncorner edge.  Offset slides the plate along the corner edge.\nCopies places N plates spaced with the Spacing distance.': 'Die Rippe ist eine Platte, die den Winkel zwischen zwei nicht parallelen\nFlächen schließt.  Profil Rechteck oder Dreieck.  L1 und L2 sind die\nKontaktlängen auf Fläche 1 und 2, gemessen von der Kante.  Der Versatz\nschiebt die Platte entlang der Kante.\nKopien platzieren N Platten im Abstand von Spacing.',
        'Create a stiffening rib between two selected faces: an angled corner, or a flat face and a cylinder': 'Crea una nervatura di irrigidimento tra due facce selezionate: un angolo, oppure un piano e un cilindro',
        'Spacing:': 'Abstand:',

        'Rib between faces: {}': 'Rippe zwischen Flächen: {}',
        "Additive rib between faces added to '{}'.": "Additive Rippe zwischen Flächen zu '{}' hinzugefügt.",
        'Rib between faces created.': 'Rippe zwischen Flächen erstellt.',
        'Length on face 1 must be positive': 'Die Länge auf Fläche 1 muss positiv sein',
        'Length on face 2 must be positive': 'Die Länge auf Fläche 2 muss positiv sein',
        'The two faces share the same centre.': 'Die beiden Flächen haben denselben Mittelpunkt.',
        'The gap between the two faces is too small.': 'Der Abstand zwischen den beiden Flächen ist zu klein.',
        'The cylindrical face could not be read.': 'Die zylindrische Fläche konnte nicht gelesen werden.',
        'The rib is a vertical plate from the planar face up against the cylinder.  Copies places N ribs rotated around the cylinder axis.  Offset slides the plate along the axis.': 'Die Rippe ist eine vertikale Platte von der ebenen Fläche zum Zylinder.\nKopien setzt N Rippen um die Zylinderachse gedreht.\nVersatz verschiebt die Platte entlang der Achse.',
        "Create Rib": "Rippe erstellen",
        "Create a stiffening rib from a sketch profile, extruded perpendicular to the sketch plane": "Eine Versteifungsrippe aus einem Skizzenprofil erstellen, das senkrecht zur Skizzenebene extrudiert wird",
        "Create a rib from a selected sketch": "Eine Rippe aus einer ausgewählten Skizze erstellen",
        "Subtractive Rib": "Subtraktive Rippe",
        "Remove a rib from the body: extrude a sketch profile perpendicular to the plane and subtract it": "Eine Rippe aus dem Körper entfernen: Skizzenprofil senkrecht zur Ebene extrudieren und subtrahieren",
        "Subtract a rib-shaped volume from the body": "Ein rippenförmiges Volumen vom Körper subtrahieren",
        "Thickness:": "Dicke:",
        "Midplane:": "Mittelebene:",
        "Reversed:": "Umgekehrt:",
        "Invert leg 1:": "Bein 1 umkehren:",
        "Invert leg 2:": "Bein 2 umkehren:",
        "Thickness is applied perpendicular to the sketch plane.\nMidplane: thickness extends equally on both sides.\nReversed: flip the normal direction.": "Die Dicke wird senkrecht zur Skizzenebene aufgebracht.\nMittelebene: Die Dicke erstreckt sich gleichmäßig auf beide Seiten.\nUmgekehrt: Normalenrichtung umkehren.",
        "Select a sketch as the rib profile.": "Wählen Sie eine Skizze als Rippenprofil.",
        "Additive rib added to '{}'.": "Additive Rippe zu '{}' hinzugefügt.",
        "Subtractive rib removed from '{}'.": "Subtraktive Rippe von '{}' entfernt.",
        "Subtractive rib needs a PartDesign body to cut.": "Die subtraktive Rippe benötigt einen PartDesign-Körper zum Schneiden.",
        "Rib created.": "Rippe erstellt.",
        "Thickness must be positive": "Die Dicke muss positiv sein",
        "The profile is degenerate: it has no area to extrude. Draw a closed profile or an open profile with more than one edge.": "Das Profil ist degeneriert: keine Fläche zum Extrudieren vorhanden. Zeichnen Sie ein geschlossenes Profil oder ein offenes Profil mit mehr als einer Kante.",
        "The profile is degenerate: it has no area to extrude. A single straight line cannot form a rib; use at least two connected edges, an arc, or a closed profile.": "Das Profil ist degeneriert: keine Fläche zum Extrudieren vorhanden. Eine einzelne gerade Linie kann keine Rippe bilden; verwenden Sie mindestens zwei verbundene Kanten, einen Bogen oder ein geschlossenes Profil.",
        "Rib: {}": "Rippe: {}",
        "Create Pipe": "Rohr erstellen",
        "Create a parametric pipe sweeping a profile along a sketch or edge path":
            "Ein parametrisches Rohr erstellen, das ein Profil entlang einer Skizze oder eines Kantenpfads zieht",
        "Create a pipe along a selected sketch or edges":
            "Ein Rohr entlang einer ausgewählten Skizze oder Kanten erstellen",
        "Subtractive Pipe": "Subtraktives Rohr",
        "Remove a pipe from the body: sweep a profile along a path and subtract it":
            "Ein Rohr aus dem Körper entfernen: Profil entlang eines Pfads ziehen und subtrahieren",
        "Subtract a pipe-shaped volume from the selected body":
            "Ein rohrförmiges Volumen vom ausgewählten Körper subtrahieren",
        "Assembly Cut": "Baugruppen-Schnitt",
        "Cut several PartDesign bodies at once using one sketch":
            "Mehrere PartDesign-Körper gleichzeitig mit einer Skizze schneiden",
        "Cut multiple bodies with a single sketch":
            "Mehrere Körper mit einer einzigen Skizze schneiden",
        "Weight / Volume": "Gewicht / Volumen",
        "Compute the volume and the weight of a body with a material density selector":
            "Volumen und Gewicht eines Körpers mit einem Materialdichte-Auswahl berechnen",
        "Show volume and mass of the selected body":
            "Volumen und Masse des ausgewählten Körpers anzeigen",
        "Part Design Upgrade": "Part Design Upgrade",
        "PartDesign helpers: pipe, assembly cut and weight/volume":
            "PartDesign-Helfer: Rohr, Baugruppen-Schnitt und Gewicht/Volumen",
        "Profile shape:": "Profilform:",
        "Circle": "Kreis",
        "Square": "Quadrat",
        "Triangle": "Dreieck",
        "Pentagon": "Fünfeck",
        "Hexagon": "Sechseck",
        "Octagon": "Achteck",
        "Side length:": "Seitenlänge:",
        "Radius:": "Radius:",
        "Wall thickness:": "Wandstärke:",
        "Rotation:": "Rotation:",
        "Corner transition:": "Eckenübergang:",
        "Profile offset": "Profilversatz",
        "Center": "Zentrieren",
        "Rotation turns the cross-section around the pipe axis.\nOffset (0 = centered on the path): X moves the profile sideways,\nY moves it up/down (both also negative).\nWall thickness (0 = solid): hollows out the pipe, keeping the\ndimension above as the EXTERNAL size.":
            "Die Rotation dreht den Querschnitt um die Rohrachse.\nVersatz (0 = zentriert auf dem Pfad): X verschiebt das Profil seitlich,\nY nach oben/unten (auch negativ).\nWandstärke (0 = massiv): macht das Rohr hohl, wobei die obige\nAbmessung die AUSSENGRÖSSE bleibt.",
        "Preview": "Vorschau",
        "Show final result": "Endresultat anzeigen",
        "Show overlapping preview": "Überlagerte Vorschau anzeigen",
        "Right corner": "Rechte Ecke",
        "Round corner": "Runde Ecke",
        "Transformed": "Transformiert",
        "No active document": "Kein aktives Dokument",
        "Select a sketch, or one or more edges of a body, as the pipe path.":
            "Wählen Sie eine Skizze oder eine oder mehrere Kanten eines Körpers als Rohrpfad.",
        "The selected sketch is empty.": "Die ausgewählte Skizze ist leer.",
        "The selected edges do not form a connected path: {}":
            "Die ausgewählten Kanten bilden keinen verbundenen Pfad: {}",
        "Additive pipe added to '{}'.": "Additives Rohr zu '{}' hinzugefügt.",
        "Subtractive pipe removed from '{}'.": "Subtraktives Rohr von '{}' entfernt.",
        "Subtractive pipe needs a PartDesign body to cut.":
            "Das subtraktive Rohr benötigt einen PartDesign-Körper zum Schneiden.",
        "Pipe created.": "Rohr erstellt.",
        "Wall thickness too large for the profile: keeping a solid pipe.":
            "Wandstärke zu groß für das Profil: Es bleibt ein massives Rohr.",
        "Pipe sweep truncated on this path (volume {:.1f}, expected ~{:.1f}). Reduce the profile size or offset, or round the path corners.":
            "Rohr-Sweep auf diesem Pfad abgeschnitten (Volumen {:.1f}, erwartet ~{:.1f}). Profilgröße oder Versatz verringern oder Pfadecken abrunden.",
        "Note: corner transition '{}' is not possible at this profile rotation; using '{}' (profile rotation left unchanged).":
            "Hinweis: Eckenübergang '{}' ist bei dieser Profilrotation nicht möglich; verwende '{}' (Profilrotation unverändert).",
        "Could not sweep the profile along the path (degenerate result). Try changing the profile size or smoothing the path corners.":
            "Profil entlang des Pfads kann nicht gesweept werden (degeneriertes Ergebnis). Profilgröße ändern oder Pfadecken glätten.",
        "Body:": "Körper:",
        "Object:": "Objekt:",
        "Volume:": "Volumen:",
        "Material:": "Material:",
        "Custom density:": "Benutzerdefinierte Dichte:",
        "Mass: {:.3f} g   ({:.6f} kg)": "Masse: {:.3f} g   ({:.6f} kg)",
        "Total ({} parts): {:.3f} g   ({:.3f} cm\u00b3)":
            "Gesamt ({} Teile): {:.3f} g   ({:.3f} cm\u00b3)",
        "Part": "Teil",
        "Material": "Material",
        "Mass (g)": "Masse (g)",
        "Each part keeps its own material. 'Total' sums every part\nwith the material assigned to each one. Selecting a body in\nthe 3D view (or clicking a row) selects it here.":
            "Jedes Teil behält sein eigenes Material. 'Gesamt' summiert jedes Teil\nmit dem jeweils zugewiesenen Material. Die Auswahl eines Körpers in\nder 3D-Ansicht (oder ein Klick auf eine Zeile) wählt ihn hier aus.",
        "Select a PartDesign body or a shape with volume first.":
            "Wählen Sie zuerst einen PartDesign-Körper oder eine Form mit Volumen.",
        "Sketch: ": "Skizze: ",
        "Select bodies to cut (reorder with arrows):":
            "Zu schneidende Körper auswählen (mit Pfeilen umsortieren):",
        "Mode:": "Modus:",
        "Independent sketches (full copy)": "Unabhängige Skizzen (vollständige Kopie)",
        "Binder (linked to sketch)": "Binder (mit der Skizze verknüpft)",
        "Each body gets an independent copy of the sketch.":
            "Jeder Körper erhält eine unabhängige Kopie der Skizze.",
        "Each body gets a binder linked to the original sketch.":
            "Jeder Körper erhält einen Binder, der mit der Originalskizze verknüpft ist.",
        "Cut Bodies": "Körper schneiden",
        "Cancel": "Abbrechen",
        "Select All": "Alle auswählen",
        "Deselect All": "Auswahl aufheben",
        "No active document.": "Kein aktives Dokument.",
        "Select a Sketch first, then run this command.":
            "Wählen Sie zuerst eine Skizze aus und starten Sie dann diesen Befehl.",
        "No PartDesign::Body found in document.":
            "Kein PartDesign::Body im Dokument gefunden.",
        "Error creating profile for ": "Fehler beim Erstellen des Profils für ",
        "Export CSV…": "CSV exportieren…",
        "Save the part list with material and mass as a CSV file.":
            "Teileliste mit Material und Masse als CSV-Datei speichern.",
        "Export BOM as CSV": "Stückliste als CSV exportieren",
        "CSV files (*.csv)": "CSV-Dateien (*.csv)",
        "Volume (cm\u00b3)": "Volumen (cm\u00b3)",
        "Density (kg/m\u00b3)": "Dichte (kg/m\u00b3)",
        "Total": "Gesamt",
        "Unable to write file:\n{}": "Datei kann nicht geschrieben werden:\n{}",
        "BOM exported to:\n{}": "Stückliste exportiert nach:\n{}",
    },
    "es": {
        'Rectangle': 'RectÃ¡ngulo',
        'Triangle': 'TriÃ¡ngulo',
        'Rotation angle (Â°):': 'Ã\x81ngulo de rotaciÃ³n (Â°):',
        'The rib is a plate closing the corner between the planar\nface and the cylinder, like between two non-parallel\nsurfaces.  Rectangle or Triangle profile.  Copies places N\nplates rotated around the cylinder axis.  The inner edge\nsinks into the cylinder until both its corners touch the\ncylinder surface.  Angle rotates the ribs around the axis\nto position them where wanted.': 'La nervadura es una placa que cierra el ángulo entre el plano y el cilindro,\ncomo entre dos superficies no paralelas.  Perfil Rectángulo o Triángulo.\nLas copias colocan N placas giradas alrededor del eje del cilindro.  El borde\ninterior se hunde en el cilindro hasta que sus dos ángulos tocan la superficie.\nEl ángulo gira las nervaduras alrededor del eje para colocarlas donde se desee.',

        'Full face length': 'Longitud en toda la cara',
        'Create Rib Between Faces': 'Crear nervio entre caras',
        'Create a rib between two selected faces': 'Crear un nervio entre dos caras seleccionadas',
        'Length on face 1:': 'Longitud en la cara 1:',
        'Length on face 2:': 'Longitud en la cara 2:',
        'Offset:': 'Desplazamiento:',
        'Copies:': 'Copias:',
        'Select exactly two faces.': 'Seleccione exactamente dos caras.',
        'The faces are not usable: select two angled planar faces, or a planar face and a cylinder.': 'Las caras no son utilizables: seleccione dos caras planas, o una cara plana y un cilindro.',
        'The rib is a plate closing the angle between two non-parallel\nplanar faces.  Rectangle or Triangle profile.  L1 and L2 are\nthe contact lengths on faces 1 and 2, measured from the\ncorner edge.  Offset slides the plate along the corner edge.\nCopies places N plates spaced with the Spacing distance.': 'La nervadura es una placa que cierra el ángulo entre dos caras no paralelas.\nPerfil Rectángulo o Triángulo.  L1 y L2 son las longitudes de contacto\nen las caras 1 y 2, medidas desde el borde.  El desplazamiento desliza la\nplaca a lo largo del borde.\nLas copias colocan N placas separadas por la distancia Espaciado.',
        'Create a stiffening rib between two selected faces: an angled corner, or a flat face and a cylinder': 'Crea una nervatura di irrigidimento tra due facce selezionate: un angolo, oppure un piano e un cilindro',
        'Spacing:': 'Espaciado:',

        'Rib between faces: {}': 'Nervio entre caras: {}',
        "Additive rib between faces added to '{}'.": "Nervio aditivo entre caras añadido a '{}'.",
        'Rib between faces created.': 'Nervio entre caras creado.',
        'Length on face 1 must be positive': 'La longitud en la cara 1 debe ser positiva',
        'Length on face 2 must be positive': 'La longitud en la cara 2 debe ser positiva',
        'The two faces share the same centre.': 'Las dos caras comparten el mismo centro.',
        'The gap between the two faces is too small.': 'La separación entre las dos caras es demasiado pequeña.',
        'The cylindrical face could not be read.': 'No se pudo leer la cara cilíndrica.',
        'The rib is a vertical plate from the planar face up against the cylinder.  Copies places N ribs rotated around the cylinder axis.  Offset slides the plate along the axis.': 'El nervio es una placa vertical desde el plano hasta el cilindro.\nCopias coloca N nervios girados alrededor del eje del cilindro.\nEl desplazamiento desliza la placa a lo largo del eje.',
        "Create Rib": "Crear nervadura",
        "Create a stiffening rib from a sketch profile, extruded perpendicular to the sketch plane": "Crear una nervadura de refuerzo a partir de un perfil de croquis, extruido perpendicularmente al plano del croquis",
        "Create a rib from a selected sketch": "Crear una nervadura a partir de un croquis seleccionado",
        "Subtractive Rib": "Nervadura sustractiva",
        "Remove a rib from the body: extrude a sketch profile perpendicular to the plane and subtract it": "Eliminar una nervadura del cuerpo: extruir un perfil de croquis perpendicularmente al plano y restarlo",
        "Subtract a rib-shaped volume from the body": "Restar un volumen en forma de nervadura del cuerpo",
        "Thickness:": "Grosor:",
        "Midplane:": "Plano medio:",
        "Reversed:": "Invertido:",
        "Invert leg 1:": "Invertir lado 1:",
        "Invert leg 2:": "Invertir lado 2:",
        "Thickness is applied perpendicular to the sketch plane.\nMidplane: thickness extends equally on both sides.\nReversed: flip the normal direction.": "El grosor se aplica perpendicularmente al plano del croquis.\nPlano medio: el grosor se extiende por igual a ambos lados.\nInvertido: invierte la dirección de la normal.",
        "Select a sketch as the rib profile.": "Seleccione un croquis como perfil de nervadura.",
        "Additive rib added to '{}'.": "Nervadura aditiva añadida a '{}'.",
        "Subtractive rib removed from '{}'.": "Nervadura sustractiva eliminada de '{}'.",
        "Subtractive rib needs a PartDesign body to cut.": "La nervadura sustractiva necesita un cuerpo PartDesign para cortar.",
        "Rib created.": "Nervadura creada.",
        "Thickness must be positive": "El grosor debe ser positivo",
        "The profile is degenerate: it has no area to extrude. Draw a closed profile or an open profile with more than one edge.": "El perfil es degenerado: no tiene área para extruir. Dibuje un perfil cerrado o un perfil abierto con más de un borde.",
        "The profile is degenerate: it has no area to extrude. A single straight line cannot form a rib; use at least two connected edges, an arc, or a closed profile.": "El perfil es degenerado: no tiene área para extruir. Una línea recta única no puede formar una nervadura; use al menos dos bordes conectados, un arco o un perfil cerrado.",
        "Rib: {}": "Nervadura: {}",
        "Create Pipe": "Crear tubería",
        "Create a parametric pipe sweeping a profile along a sketch or edge path":
            "Crear una tubería paramétrica que barre un perfil a lo largo de un croquis o de un camino de aristas",
        "Create a pipe along a selected sketch or edges":
            "Crear una tubería a lo largo de un croquis o de aristas seleccionadas",
        "Subtractive Pipe": "Tubería sustractiva",
        "Remove a pipe from the body: sweep a profile along a path and subtract it":
            "Eliminar una tubería del cuerpo: barrer un perfil a lo largo de un camino y restarlo",
        "Subtract a pipe-shaped volume from the selected body":
            "Restar un volumen con forma de tubería del cuerpo seleccionado",
        "Assembly Cut": "Corte de ensamblaje",
        "Cut several PartDesign bodies at once using one sketch":
            "Cortar varios cuerpos PartDesign a la vez usando un solo croquis",
        "Cut multiple bodies with a single sketch":
            "Cortar varios cuerpos con un solo croquis",
        "Weight / Volume": "Peso / Volumen",
        "Compute the volume and the weight of a body with a material density selector":
            "Calcular el volumen y el peso de un cuerpo con un selector de densidad de material",
        "Show volume and mass of the selected body":
            "Mostrar el volumen y la masa del cuerpo seleccionado",
        "Part Design Upgrade": "Part Design Upgrade",
        "PartDesign helpers: pipe, assembly cut and weight/volume":
            "Utilidades de PartDesign: tubería, corte de ensamblaje y peso/volumen",
        "Profile shape:": "Forma del perfil:",
        "Circle": "Círculo",
        "Square": "Cuadrado",
        "Triangle": "Triángulo",
        "Pentagon": "Pentágono",
        "Hexagon": "Hexágono",
        "Octagon": "Octógono",
        "Side length:": "Longitud del lado:",
        "Radius:": "Radio:",
        "Wall thickness:": "Grosor de pared:",
        "Rotation:": "Rotación:",
        "Corner transition:": "Transición de esquina:",
        "Profile offset": "Desplazamiento del perfil",
        "Center": "Centrar",
        "Rotation turns the cross-section around the pipe axis.\nOffset (0 = centered on the path): X moves the profile sideways,\nY moves it up/down (both also negative).\nWall thickness (0 = solid): hollows out the pipe, keeping the\ndimension above as the EXTERNAL size.":
            "La rotación gira la sección alrededor del eje de la tubería.\nDesplazamiento (0 = centrado en el camino): X mueve el perfil lateralmente,\nY hacia arriba/abajo (también negativos).\nGrosor de pared (0 = sólido): ahueca la tubería, manteniendo la\ndimensión anterior como tamaño EXTERNO.",
        "Preview": "Vista previa",
        "Show final result": "Mostrar resultado final",
        "Show overlapping preview": "Mostrar vista previa superpuesta",
        "Right corner": "Esquina recta",
        "Round corner": "Esquina redondeada",
        "Transformed": "Transformada",
        "No active document": "No hay documento activo",
        "Select a sketch, or one or more edges of a body, as the pipe path.":
            "Seleccione un croquis, o una o más aristas de un cuerpo, como camino de la tubería.",
        "The selected sketch is empty.": "El croquis seleccionado está vacío.",
        "The selected edges do not form a connected path: {}":
            "Las aristas seleccionadas no forman un camino conectado: {}",
        "Additive pipe added to '{}'.": "Tubería aditiva añadida a '{}'.",
        "Subtractive pipe removed from '{}'.": "Tubería sustractiva eliminada de '{}'.",
        "Subtractive pipe needs a PartDesign body to cut.":
            "La tubería sustractiva necesita un cuerpo PartDesign para cortar.",
        "Pipe created.": "Tubería creada.",
        "Wall thickness too large for the profile: keeping a solid pipe.":
            "Grosor de pared demasiado grande para el perfil: se mantiene una tubería sólida.",
        "Pipe sweep truncated on this path (volume {:.1f}, expected ~{:.1f}). Reduce the profile size or offset, or round the path corners.":
            "Barrido de tubería truncado en este camino (volumen {:.1f}, esperado ~{:.1f}). Reduzca el tamaño o el desplazamiento del perfil, o redondee las esquinas del camino.",
        "Note: corner transition '{}' is not possible at this profile rotation; using '{}' (profile rotation left unchanged).":
            "Nota: la transición de esquina '{}' no es posible con esta rotación; se usa '{}' (rotación del perfil sin cambios).",
        "Could not sweep the profile along the path (degenerate result). Try changing the profile size or smoothing the path corners.":
            "No se pudo barrer el perfil a lo largo del camino (resultado degenerado). Cambie el tamaño del perfil o suavice las esquinas del camino.",
        "Body:": "Cuerpo:",
        "Object:": "Objeto:",
        "Volume:": "Volumen:",
        "Material:": "Material:",
        "Custom density:": "Densidad personalizada:",
        "Mass: {:.3f} g   ({:.6f} kg)": "Masa: {:.3f} g   ({:.6f} kg)",
        "Total ({} parts): {:.3f} g   ({:.3f} cm\u00b3)":
            "Total ({} piezas): {:.3f} g   ({:.3f} cm\u00b3)",
        "Part": "Pieza",
        "Material": "Material",
        "Mass (g)": "Masa (g)",
        "Each part keeps its own material. 'Total' sums every part\nwith the material assigned to each one. Selecting a body in\nthe 3D view (or clicking a row) selects it here.":
            "Cada pieza conserva su propio material. 'Total' suma cada pieza\ncon el material asignado a cada una. Seleccionar un cuerpo en la\nvista 3D (o hacer clic en una fila) lo selecciona aquí.",
        "Select a PartDesign body or a shape with volume first.":
            "Seleccione primero un cuerpo PartDesign o una forma con volumen.",
        "Sketch: ": "Croquis: ",
        "Select bodies to cut (reorder with arrows):":
            "Seleccione los cuerpos a cortar (reordenar con flechas):",
        "Mode:": "Modo:",
        "Independent sketches (full copy)": "Croquis independientes (copia completa)",
        "Binder (linked to sketch)": "Binder (vinculado al croquis)",
        "Each body gets an independent copy of the sketch.":
            "Cada cuerpo recibe una copia independiente del croquis.",
        "Each body gets a binder linked to the original sketch.":
            "Cada cuerpo recibe un binder vinculado al croquis original.",
        "Cut Bodies": "Cortar cuerpos",
        "Cancel": "Cancelar",
        "Select All": "Seleccionar todo",
        "Deselect All": "Desmarcar todo",
        "No active document.": "No hay documento activo.",
        "Select a Sketch first, then run this command.":
            "Seleccione primero un croquis y luego ejecute este comando.",
        "No PartDesign::Body found in document.":
            "No se encontró ningún PartDesign::Body en el documento.",
        "Error creating profile for ": "Error al crear el perfil para ",
        "Export CSV…": "Exportar CSV…",
        "Save the part list with material and mass as a CSV file.":
            "Guardar la lista de piezas con material y masa en un archivo CSV.",
        "Export BOM as CSV": "Exportar BOM como CSV",
        "CSV files (*.csv)": "Archivos CSV (*.csv)",
        "Volume (cm\u00b3)": "Volumen (cm\u00b3)",
        "Density (kg/m\u00b3)": "Densidad (kg/m\u00b3)",
        "Total": "Total",
        "Unable to write file:\n{}": "No se puede escribir el archivo:\n{}",
        "BOM exported to:\n{}": "BOM exportada a:\n{}",
    },
    "pt": {
        'Rectangle': 'RetÃ¢ngulo',
        'Triangle': 'TriÃ¢ngulo',
        'Rotation angle (Â°):': 'Ã\x82ngulo de rotaÃ§Ã£o (Â°):',
        'The rib is a plate closing the corner between the planar\nface and the cylinder, like between two non-parallel\nsurfaces.  Rectangle or Triangle profile.  Copies places N\nplates rotated around the cylinder axis.  The inner edge\nsinks into the cylinder until both its corners touch the\ncylinder surface.  Angle rotates the ribs around the axis\nto position them where wanted.': 'A nervura é uma placa que fecha o ângulo entre o plano e o cilindro,\ncomo entre duas superfícies não paralelas.  Perfil Retângulo ou Triângulo.\nAs cópias colocam N placas giradas em torno do eixo do cilindro.  A borda\ninterna afunda no cilindro até que ambos os cantos toquem a superfície.\nO ângulo gira as nervuras em torno do eixo para posicioná-las onde quiser.',

        'Full face length': 'Comprimento em toda a face',
        'Create Rib Between Faces': 'Criar nervura entre faces',
        'Create a rib between two selected faces': 'Criar uma nervura entre duas faces selecionadas',
        'Length on face 1:': 'Comprimento na face 1:',
        'Length on face 2:': 'Comprimento na face 2:',
        'Offset:': 'Deslocamento:',
        'Copies:': 'Cópias:',
        'Select exactly two faces.': 'Selecione exatamente duas faces.',
        'The faces are not usable: select two angled planar faces, or a planar face and a cylinder.': 'As faces não são utilizáveis: selecione duas faces planas, ou uma face plana e um cilindro.',
        'The rib is a plate closing the angle between two non-parallel\nplanar faces.  Rectangle or Triangle profile.  L1 and L2 are\nthe contact lengths on faces 1 and 2, measured from the\ncorner edge.  Offset slides the plate along the corner edge.\nCopies places N plates spaced with the Spacing distance.': 'A nervura é uma placa que fecha o ângulo entre duas faces não paralelas.\nPerfil Retângulo ou Triângulo.  L1 e L2 são os comprimentos de contato\nnas faces 1 e 2, medidos a partir da borda.  O deslocamento desliza a placa\nao longo da borda.\nAs cópias colocam N placas separadas pela distância Espaçamento.',
        'Create a stiffening rib between two selected faces: an angled corner, or a flat face and a cylinder': 'Crea una nervatura di irrigidimento tra due facce selezionate: un angolo, oppure un piano e un cilindro',
        'Spacing:': 'Espaçamento:',

        'Rib between faces: {}': 'Nervura entre faces: {}',
        "Additive rib between faces added to '{}'.": "Nervura aditiva entre faces adicionada a '{}'.",
        'Rib between faces created.': 'Nervura entre faces criada.',
        'Length on face 1 must be positive': 'O comprimento na face 1 deve ser positivo',
        'Length on face 2 must be positive': 'O comprimento na face 2 deve ser positivo',
        'The two faces share the same centre.': 'As duas faces partilham o mesmo centro.',
        'The gap between the two faces is too small.': 'O espaço entre as duas faces é demasiado pequeno.',
        'The cylindrical face could not be read.': 'Não foi possível ler a face cilíndrica.',
        'The rib is a vertical plate from the planar face up against the cylinder.  Copies places N ribs rotated around the cylinder axis.  Offset slides the plate along the axis.': 'A nervura é uma placa vertical do plano até ao cilindro.\nCópias coloca N nervuras giradas em torno do eixo do cilindro.\nO deslocamento desliza a placa ao longo do eixo.',
        "Create Rib": "Criar nervura",
        "Create a stiffening rib from a sketch profile, extruded perpendicular to the sketch plane": "Criar uma nervura de reforço a partir de um perfil de esboço, extrudido perpendicularmente ao plano do esboço",
        "Create a rib from a selected sketch": "Criar uma nervura a partir de um esboço selecionado",
        "Subtractive Rib": "Nervura subtrativa",
        "Remove a rib from the body: extrude a sketch profile perpendicular to the plane and subtract it": "Remover uma nervura do corpo: extrudir um perfil de esboço perpendicularmente ao plano e subtraí-lo",
        "Subtract a rib-shaped volume from the body": "Subtrair um volume em forma de nervura do corpo",
        "Thickness:": "Espessura:",
        "Midplane:": "Plano médio:",
        "Reversed:": "Invertido:",
        "Invert leg 1:": "Inverter a perna 1:",
        "Invert leg 2:": "Inverter a perna 2:",
        "Thickness is applied perpendicular to the sketch plane.\nMidplane: thickness extends equally on both sides.\nReversed: flip the normal direction.": "A espessura é aplicada perpendicularmente ao plano do esboço.\nPlano médio: a espessura estende-se igualmente em ambos os lados.\nInvertido: inverte a direção da normal.",
        "Select a sketch as the rib profile.": "Selecione um esboço como perfil de nervura.",
        "Additive rib added to '{}'.": "Nervura aditiva adicionada a '{}'.",
        "Subtractive rib removed from '{}'.": "Nervura subtrativa removida de '{}'.",
        "Subtractive rib needs a PartDesign body to cut.": "A nervura subtrativa precisa de um corpo PartDesign para cortar.",
        "Rib created.": "Nervura criada.",
        "Thickness must be positive": "A espessura deve ser positiva",
        "The profile is degenerate: it has no area to extrude. Draw a closed profile or an open profile with more than one edge.": "O perfil é degenerado: não tem área para extrudir. Desenhe um perfil fechado ou um perfil aberto com mais de uma aresta.",
        "The profile is degenerate: it has no area to extrude. A single straight line cannot form a rib; use at least two connected edges, an arc, or a closed profile.": "O perfil é degenerado: não tem área para extrudir. Uma única linha reta não pode formar uma nervura; use pelo menos duas arestas conectadas, um arco ou um perfil fechado.",
        "Rib: {}": "Nervura: {}",
        "Create Pipe": "Criar tubo",
        "Create a parametric pipe sweeping a profile along a sketch or edge path":
            "Criar um tubo paramétrico que varre um perfil ao longo de um esboço ou de um caminho de arestas",
        "Create a pipe along a selected sketch or edges":
            "Criar um tubo ao longo de um esboço ou de arestas selecionadas",
        "Subtractive Pipe": "Tubo subtrativo",
        "Remove a pipe from the body: sweep a profile along a path and subtract it":
            "Remover um tubo do corpo: varrer um perfil ao longo de um caminho e subtraí-lo",
        "Subtract a pipe-shaped volume from the selected body":
            "Subtrair um volume em forma de tubo do corpo selecionado",
        "Assembly Cut": "Corte de montagem",
        "Cut several PartDesign bodies at once using one sketch":
            "Cortar vários corpos PartDesign de uma vez usando um único esboço",
        "Cut multiple bodies with a single sketch":
            "Cortar vários corpos com um único esboço",
        "Weight / Volume": "Peso / Volume",
        "Compute the volume and the weight of a body with a material density selector":
            "Calcular o volume e o peso de um corpo com um seletor de densidade de material",
        "Show volume and mass of the selected body":
            "Mostrar o volume e a massa do corpo selecionado",
        "Part Design Upgrade": "Part Design Upgrade",
        "PartDesign helpers: pipe, assembly cut and weight/volume":
            "Utilitários PartDesign: tubo, corte de montagem e peso/volume",
        "Profile shape:": "Forma do perfil:",
        "Circle": "Círculo",
        "Square": "Quadrado",
        "Triangle": "Triângulo",
        "Pentagon": "Pentágono",
        "Hexagon": "Hexágono",
        "Octagon": "Octógono",
        "Side length:": "Comprimento do lado:",
        "Radius:": "Raio:",
        "Wall thickness:": "Espessura da parede:",
        "Rotation:": "Rotação:",
        "Corner transition:": "Transição de canto:",
        "Profile offset": "Desvio do perfil",
        "Center": "Centrar",
        "Rotation turns the cross-section around the pipe axis.\nOffset (0 = centered on the path): X moves the profile sideways,\nY moves it up/down (both also negative).\nWall thickness (0 = solid): hollows out the pipe, keeping the\ndimension above as the EXTERNAL size.":
            "A rotação gira a secção em torno do eixo do tubo.\nDesvio (0 = centrado no caminho): X move o perfil lateralmente,\nY para cima/baixo (também negativos).\nEspessura da parede (0 = sólido): torna o tubo oco, mantendo a\ndimensão acima como tamanho EXTERNO.",
        "Preview": "Pré-visualização",
        "Show final result": "Mostrar resultado final",
        "Show overlapping preview": "Mostrar pré-visualização sobreposta",
        "Right corner": "Canto reto",
        "Round corner": "Canto arredondado",
        "Transformed": "Transformada",
        "No active document": "Nenhum documento ativo",
        "Select a sketch, or one or more edges of a body, as the pipe path.":
            "Selecione um esboço, ou uma ou mais arestas de um corpo, como caminho do tubo.",
        "The selected sketch is empty.": "O esboço selecionado está vazio.",
        "The selected edges do not form a connected path: {}":
            "As arestas selecionadas não formam um caminho conectado: {}",
        "Additive pipe added to '{}'.": "Tubo aditivo adicionado a '{}'.",
        "Subtractive pipe removed from '{}'.": "Tubo subtrativo removido de '{}'.",
        "Subtractive pipe needs a PartDesign body to cut.":
            "O tubo subtrativo precisa de um corpo PartDesign para cortar.",
        "Pipe created.": "Tubo criado.",
        "Wall thickness too large for the profile: keeping a solid pipe.":
            "Espessura da parede demasiado grande para o perfil: mantém-se um tubo sólido.",
        "Pipe sweep truncated on this path (volume {:.1f}, expected ~{:.1f}). Reduce the profile size or offset, or round the path corners.":
            "Varredura do tubo truncada neste caminho (volume {:.1f}, esperado ~{:.1f}). Reduza o tamanho ou desvio do perfil, ou arredonde os cantos do caminho.",
        "Note: corner transition '{}' is not possible at this profile rotation; using '{}' (profile rotation left unchanged).":
            "Nota: a transição de canto '{}' não é possível com esta rotação; a usar '{}' (rotação do perfil inalterada).",
        "Could not sweep the profile along the path (degenerate result). Try changing the profile size or smoothing the path corners.":
            "Não foi possível varrer o perfil ao longo do caminho (resultado degenerado). Mude o tamanho do perfil ou suavize os cantos do caminho.",
        "Body:": "Corpo:",
        "Object:": "Objeto:",
        "Volume:": "Volume:",
        "Material:": "Material:",
        "Custom density:": "Densidade personalizada:",
        "Mass: {:.3f} g   ({:.6f} kg)": "Massa: {:.3f} g   ({:.6f} kg)",
        "Total ({} parts): {:.3f} g   ({:.3f} cm\u00b3)":
            "Total ({} peças): {:.3f} g   ({:.3f} cm\u00b3)",
        "Part": "Peça",
        "Material": "Material",
        "Mass (g)": "Massa (g)",
        "Each part keeps its own material. 'Total' sums every part\nwith the material assigned to each one. Selecting a body in\nthe 3D view (or clicking a row) selects it here.":
            "Cada peça mantém o seu próprio material. 'Total' soma cada peça\ncom o material atribuído a cada uma. Selecionar um corpo na\nvista 3D (ou clicar numa linha) seleciona-o aqui.",
        "Select a PartDesign body or a shape with volume first.":
            "Selecione primeiro um corpo PartDesign ou uma forma com volume.",
        "Sketch: ": "Esboço: ",
        "Select bodies to cut (reorder with arrows):":
            "Selecione os corpos a cortar (reordenar com setas):",
        "Mode:": "Modo:",
        "Independent sketches (full copy)": "Esboços independentes (cópia completa)",
        "Binder (linked to sketch)": "Binder (ligado ao esboço)",
        "Each body gets an independent copy of the sketch.":
            "Cada corpo recebe uma cópia independente do esboço.",
        "Each body gets a binder linked to the original sketch.":
            "Cada corpo recebe um binder ligado ao esboço original.",
        "Cut Bodies": "Cortar corpos",
        "Cancel": "Cancelar",
        "Select All": "Selecionar tudo",
        "Deselect All": "Desmarcar tudo",
        "No active document.": "Nenhum documento ativo.",
        "Select a Sketch first, then run this command.":
            "Selecione primeiro um esboço e depois execute este comando.",
        "No PartDesign::Body found in document.":
            "Nenhum PartDesign::Body encontrado no documento.",
        "Error creating profile for ": "Erro ao criar o perfil para ",
        "Export CSV…": "Exportar CSV…",
        "Save the part list with material and mass as a CSV file.":
            "Guardar a lista de peças com material e massa num ficheiro CSV.",
        "Export BOM as CSV": "Exportar BOM como CSV",
        "CSV files (*.csv)": "Ficheiros CSV (*.csv)",
        "Volume (cm\u00b3)": "Volume (cm\u00b3)",
        "Density (kg/m\u00b3)": "Densidade (kg/m\u00b3)",
        "Total": "Total",
        "Unable to write file:\n{}": "Não é possível escrever o ficheiro:\n{}",
        "BOM exported to:\n{}": "BOM exportada para:\n{}",
    },
    "pl": {
        'Rectangle': 'ProstokÄ\x85t',
        'Triangle': 'TrÃ³jkÄ\x85t',
        'Rotation angle (Â°):': 'KÄ\x85t obrotu (Â°):',
        'The rib is a plate closing the corner between the planar\nface and the cylinder, like between two non-parallel\nsurfaces.  Rectangle or Triangle profile.  Copies places N\nplates rotated around the cylinder axis.  The inner edge\nsinks into the cylinder until both its corners touch the\ncylinder surface.  Angle rotates the ribs around the axis\nto position them where wanted.': 'Żebro to płyta zamykająca narożnik między płaszczyzną a\ncylindrem, jak między dwiema nierównoległymi powierzchniami.  Profil\nProstokąt lub Trójkąt.  Kopie umieszczają N płyt wokół osi.\nWewnętrzna krawędź wchodzi w cylinder, aż oba rogi dotykają powierzchni.\nKąt obraca żebra wokół osi, aby ustawić je w dowolnym miejscu.',

        'Full face length': 'Długość na całej ścianie',
        'Create Rib Between Faces': 'Utwórz żebro między ścianami',
        'Create a rib between two selected faces': 'Utwórz żebro między dwiema wybranymi ścianami',
        'Length on face 1:': 'Długość na ścianie 1:',
        'Length on face 2:': 'Długość na ścianie 2:',
        'Offset:': 'Przesunięcie:',
        'Copies:': 'Kopie:',
        'Select exactly two faces.': 'Wybierz dokładnie dwie ściany.',
        'The faces are not usable: select two angled planar faces, or a planar face and a cylinder.': 'Ściany nie nadają się: wybierz dwie płaskie ściany albo płaską ścianę i walec.',
        'The rib is a plate closing the angle between two non-parallel\nplanar faces.  Rectangle or Triangle profile.  L1 and L2 are\nthe contact lengths on faces 1 and 2, measured from the\ncorner edge.  Offset slides the plate along the corner edge.\nCopies places N plates spaced with the Spacing distance.': 'Żebro to płyta zamykająca kąt między dwiema nierównoległymi\npłaszczyznami.  Profil Prostokąt lub Trójkąt.  L1 i L2 to długości\nkontaktu na ścianach 1 i 2, mierzone od krawędzi.  Przesunięcie przesuwa\npłytę wzdłuż krawędzi.\nKopie umieszczają N płyt w odstępach co Spacing.',
        'Create a stiffening rib between two selected faces: an angled corner, or a flat face and a cylinder': 'Crea una nervatura di irrigidimento tra due facce selezionate: un angolo, oppure un piano e un cilindro',
        'Spacing:': 'Odstęp:',

        'Rib between faces: {}': 'Żebro między ścianami: {}',
        "Additive rib between faces added to '{}'.": "Dodano addytywne żebro między ścianami do '{}'.",
        'Rib between faces created.': 'Utworzono żebro między ścianami.',
        'Length on face 1 must be positive': 'Długość na ścianie 1 musi być dodatnia',
        'Length on face 2 must be positive': 'Długość na ścianie 2 musi być dodatnia',
        'The two faces share the same centre.': 'Obie ściany mają ten sam środek.',
        'The gap between the two faces is too small.': 'Odstęp między ścianami jest zbyt mały.',
        'The cylindrical face could not be read.': 'Nie można odczytać powierzchni cylindrycznej.',
        'The rib is a vertical plate from the planar face up against the cylinder.  Copies places N ribs rotated around the cylinder axis.  Offset slides the plate along the axis.': 'Żebro to pionowa płyta od płaszczyzny do walca.\nKopie umieszcza N żeber obróconych wokół osi walca.\nPrzesunięcie przesuwa płytę wzdłuż osi.',
        "Create Rib": "Utwórz żebro",
        "Create a stiffening rib from a sketch profile, extruded perpendicular to the sketch plane": "Utwórz żebro usztywniające z profilu szkicu, wyciągniętego prostopadle do płaszczyzny szkicu",
        "Create a rib from a selected sketch": "Utwórz żebro z wybranego szkicu",
        "Subtractive Rib": "Żebro subtraktywne",
        "Remove a rib from the body: extrude a sketch profile perpendicular to the plane and subtract it": "Usuń żebro z bryły: wyciągnij profil szkicu prostopadle do płaszczyzny i odejmij go",
        "Subtract a rib-shaped volume from the body": "Odejmij objętość w kształcie żebra od bryły",
        "Thickness:": "Grubość:",
        "Midplane:": "Płaszczyzna środkowa:",
        "Reversed:": "Odwrócony:",
        "Invert leg 1:": "Odwróć nogę 1:",
        "Invert leg 2:": "Odwróć nogę 2:",
        "Thickness is applied perpendicular to the sketch plane.\nMidplane: thickness extends equally on both sides.\nReversed: flip the normal direction.": "Grubość jest nakładana prostopadle do płaszczyzny szkicu.\nPłaszczyzna środkowa: grubość rozciąga się równo po obu stronach.\nOdwrócony: odwraca kierunek normalnej.",
        "Select a sketch as the rib profile.": "Wybierz szkic jako profil żebra.",
        "Additive rib added to '{}'.": "Dodano żebro addytywne do '{}'.",
        "Subtractive rib removed from '{}'.": "Usunięto żebro subtraktywne z '{}'.",
        "Subtractive rib needs a PartDesign body to cut.": "Żebro subtraktywne wymaga bryły PartDesign do wycięcia.",
        "Rib created.": "Utworzono żebro.",
        "Thickness must be positive": "Grubość musi być dodatnia",
        "The profile is degenerate: it has no area to extrude. Draw a closed profile or an open profile with more than one edge.": "Profil jest zdegenerowany: nie ma obszaru do wyciągnięcia. Narysuj profil zamknięty lub otwarty z więcej niż jedną krawędzią.",
        "The profile is degenerate: it has no area to extrude. A single straight line cannot form a rib; use at least two connected edges, an arc, or a closed profile.": "Profil jest zdegenerowany: nie ma obszaru do wyciągnięcia. Pojedyncza prosta nie może utworzyć żebra; użyj co najmniej dwóch połączonych krawędzi, łuku lub profilu zamkniętego.",
        "Rib: {}": "Żebro: {}",
        "Create Pipe": "Utwórz rurę",
        "Create a parametric pipe sweeping a profile along a sketch or edge path":
            "Utwórz parametryczną rurę przeciągającą profil wzdłuż szkicu lub ścieżki krawędzi",
        "Create a pipe along a selected sketch or edges":
            "Utwórz rurę wzdłuż wybranego szkicu lub krawędzi",
        "Subtractive Pipe": "Rura subtraktywna",
        "Remove a pipe from the body: sweep a profile along a path and subtract it":
            "Usuń rurę z bryły: przeciągnij profil wzdłuż ścieżki i odejmij go",
        "Subtract a pipe-shaped volume from the selected body":
            "Odejmij objętość w kształcie rury od wybranej bryły",
        "Assembly Cut": "Cięcie zespołu",
        "Cut several PartDesign bodies at once using one sketch":
            "Przetnij kilka brył PartDesign naraz za pomocą jednego szkicu",
        "Cut multiple bodies with a single sketch":
            "Przetnij wiele brył jednym szkicem",
        "Weight / Volume": "Waga / Objętość",
        "Compute the volume and the weight of a body with a material density selector":
            "Oblicz objętość i wagę bryły za pomocą selektora gęstości materiału",
        "Show volume and mass of the selected body":
            "Pokaż objętość i masę wybranej bryły",
        "Part Design Upgrade": "Part Design Upgrade",
        "PartDesign helpers: pipe, assembly cut and weight/volume":
            "Pomocnik PartDesign: rura, cięcie zespołu i waga/objętość",
        "Profile shape:": "Kształt profilu:",
        "Circle": "Okrąg",
        "Square": "Kwadrat",
        "Triangle": "Trójkąt",
        "Pentagon": "Pięciokąt",
        "Hexagon": "Sześciokąt",
        "Octagon": "Ośmiokąt",
        "Side length:": "Długość boku:",
        "Radius:": "Promień:",
        "Wall thickness:": "Grubość ścianki:",
        "Rotation:": "Obrót:",
        "Corner transition:": "Przejście narożnika:",
        "Profile offset": "Przesunięcie profilu",
        "Center": "Wyśrodkuj",
        "Rotation turns the cross-section around the pipe axis.\nOffset (0 = centered on the path): X moves the profile sideways,\nY moves it up/down (both also negative).\nWall thickness (0 = solid): hollows out the pipe, keeping the\ndimension above as the EXTERNAL size.":
            "Obrót skręca przekrój wokół osi rury.\nPrzesunięcie (0 = wyśrodkowane na ścieżce): X przesuwa profil na boki,\nY w górę/w dół (także ujemne).\nGrubość ścianki (0 = pełna): wydrąża rurę, zachowując powyższy\nwymiar jako wymiar ZEWNĘTRZNY.",
        "Preview": "Podgląd",
        "Show final result": "Pokaż wynik końcowy",
        "Show overlapping preview": "Pokaż nakładający się podgląd",
        "Right corner": "Prosty narożnik",
        "Round corner": "Zaokrąglony narożnik",
        "Transformed": "Transformowany",
        "No active document": "Brak aktywnego dokumentu",
        "Select a sketch, or one or more edges of a body, as the pipe path.":
            "Wybierz szkic albo jedną lub więcej krawędzi bryły jako ścieżkę rury.",
        "The selected sketch is empty.": "Wybrany szkic jest pusty.",
        "The selected edges do not form a connected path: {}":
            "Wybrane krawędzie nie tworzą połączonej ścieżki: {}",
        "Additive pipe added to '{}'.": "Dodano rurę addytywną do '{}'.",
        "Subtractive pipe removed from '{}'.": "Usunięto rurę subtraktywną z '{}'.",
        "Subtractive pipe needs a PartDesign body to cut.":
            "Rura subtraktywna wymaga bryły PartDesign do wycięcia.",
        "Pipe created.": "Utworzono rurę.",
        "Wall thickness too large for the profile: keeping a solid pipe.":
            "Grubość ścianki zbyt duża dla profilu: pozostaje rura pełna.",
        "Pipe sweep truncated on this path (volume {:.1f}, expected ~{:.1f}). Reduce the profile size or offset, or round the path corners.":
            "Przeciąganie rury obcięte na tej ścieżce (objętość {:.1f}, oczekiwana ~{:.1f}). Zmniejsz rozmiar lub przesunięcie profilu albo zaokrąglij narożniki ścieżki.",
        "Note: corner transition '{}' is not possible at this profile rotation; using '{}' (profile rotation left unchanged).":
            "Uwaga: przejście narożnika '{}' nie jest możliwe przy tym obrocie profilu; użyto '{}' (obrót profilu bez zmian).",
        "Could not sweep the profile along the path (degenerate result). Try changing the profile size or smoothing the path corners.":
            "Nie można przeciągnąć profilu wzdłuż ścieżki (wynik zdegenerowany). Zmień rozmiar profilu lub wygładź narożniki ścieżki.",
        "Body:": "Bryła:",
        "Object:": "Obiekt:",
        "Volume:": "Objętość:",
        "Material:": "Materiał:",
        "Custom density:": "Gęstość niestandardowa:",
        "Mass: {:.3f} g   ({:.6f} kg)": "Masa: {:.3f} g   ({:.6f} kg)",
        "Total ({} parts): {:.3f} g   ({:.3f} cm\u00b3)":
            "Razem ({} części): {:.3f} g   ({:.3f} cm\u00b3)",
        "Part": "Część",
        "Material": "Materiał",
        "Mass (g)": "Masa (g)",
        "Each part keeps its own material. 'Total' sums every part\nwith the material assigned to each one. Selecting a body in\nthe 3D view (or clicking a row) selects it here.":
            "Każda część ma własny materiał. 'Razem' sumuje każdą część\nz przypisanym jej materiałem. Wybranie bryły w widoku 3D\n(lub kliknięcie wiersza) wybiera ją tutaj.",
        "Select a PartDesign body or a shape with volume first.":
            "Najpierw wybierz bryłę PartDesign lub kształt z objętością.",
        "Sketch: ": "Szkic: ",
        "Select bodies to cut (reorder with arrows):":
            "Wybierz bryły do cięcia (sortuj strzałkami):",
        "Mode:": "Tryb:",
        "Independent sketches (full copy)": "Niezależne szkice (pełna kopia)",
        "Binder (linked to sketch)": "Binder (połączony ze szkicem)",
        "Each body gets an independent copy of the sketch.":
            "Każda bryła otrzymuje niezależną kopię szkicu.",
        "Each body gets a binder linked to the original sketch.":
            "Każda bryła otrzymuje binder połączony z oryginalnym szkicem.",
        "Cut Bodies": "Wytnij bryły",
        "Cancel": "Anuluj",
        "Select All": "Zaznacz wszystko",
        "Deselect All": "Odznacz wszystko",
        "No active document.": "Brak aktywnego dokumentu.",
        "Select a Sketch first, then run this command.":
            "Najpierw wybierz szkic, a następnie uruchom tę komendę.",
        "No PartDesign::Body found in document.":
            "Nie znaleziono bryły PartDesign w dokumencie.",
        "Error creating profile for ": "Błąd tworzenia profilu dla ",
        "Export CSV…": "Eksportuj CSV…",
        "Save the part list with material and mass as a CSV file.":
            "Zapisz listę części z materiałem i masą jako plik CSV.",
        "Export BOM as CSV": "Eksportuj BOM jako CSV",
        "CSV files (*.csv)": "Pliki CSV (*.csv)",
        "Volume (cm\u00b3)": "Objętość (cm\u00b3)",
        "Density (kg/m\u00b3)": "Gęstość (kg/m\u00b3)",
        "Total": "Razem",
        "Unable to write file:\n{}": "Nie można zapisać pliku:\n{}",
        "BOM exported to:\n{}": "BOM wyeksportowano do:\n{}",
    },
    "ru": {
        'Rectangle': 'Ð\x9fÑ\x80Ñ\x8fÐ¼Ð¾Ñ\x83Ð³Ð¾Ð»Ñ\x8cÐ½Ð¸Ðº',
        'Triangle': 'Ð¢Ñ\x80ÐµÑ\x83Ð³Ð¾Ð»Ñ\x8cÐ½Ð¸Ðº',
        'Rotation angle (Â°):': 'Ð£Ð³Ð¾Ð» Ð¿Ð¾Ð²Ð¾Ñ\x80Ð¾Ñ\x82Ð° (Â°):',
        'The rib is a plate closing the corner between the planar\nface and the cylinder, like between two non-parallel\nsurfaces.  Rectangle or Triangle profile.  Copies places N\nplates rotated around the cylinder axis.  The inner edge\nsinks into the cylinder until both its corners touch the\ncylinder surface.  Angle rotates the ribs around the axis\nto position them where wanted.': 'Ребро — пластина, закрывающая угол между плоскостью и\nцилиндром, как между двумя непараллельными поверхностями.\nПрофиль Прямоугольник или Треугольник.\nКопии размещают N пластин вокруг оси.  Внутренняя кромка\nвходит в цилиндр, пока оба его угла не коснутся поверхности.\nУгол поворачивает рёбра вокруг оси, чтобы расположить их в нужном месте.',

        'Full face length': 'Длина по всей грани',
        'Create Rib Between Faces': 'Создать ребро между гранями',
        'Create a rib between two selected faces': 'Создать ребро между двумя выбранными гранями',
        'Length on face 1:': 'Длина на грани 1:',
        'Length on face 2:': 'Длина на грани 2:',
        'Offset:': 'Смещение:',
        'Copies:': 'Копии:',
        'Select exactly two faces.': 'Выберите ровно две грани.',
        'The faces are not usable: select two angled planar faces, or a planar face and a cylinder.': 'Грани не подходят: выберите две плоские грани или плоскую грань и цилиндр.',
        'The rib is a plate closing the angle between two non-parallel\nplanar faces.  Rectangle or Triangle profile.  L1 and L2 are\nthe contact lengths on faces 1 and 2, measured from the\ncorner edge.  Offset slides the plate along the corner edge.\nCopies places N plates spaced with the Spacing distance.': 'Ребро — пластина, закрывающая угол между двумя\nнепараллельными плоскостями.  Профиль Прямоугольник или Треугольник.\nL1 и L2 — длины контакта на гранях 1 и 2, от кромки.  Смещение\nсдвигает пластину вдоль кромки.\nКопии размещают N пластин с интервалом Spacing.',
        'Create a stiffening rib between two selected faces: an angled corner, or a flat face and a cylinder': 'Crea una nervatura di irrigidimento tra due facce selezionate: un angolo, oppure un piano e un cilindro',
        'Spacing:': 'Расстояние:',

        'Rib between faces: {}': 'Ребро между гранями: {}',
        "Additive rib between faces added to '{}'.": "Аддитивное ребро между гранями добавлено к '{}'.",
        'Rib between faces created.': 'Ребро между гранями создано.',
        'Length on face 1 must be positive': 'Длина на грани 1 должна быть положительной',
        'Length on face 2 must be positive': 'Длина на грани 2 должна быть положительной',
        'The two faces share the same centre.': 'Обе грани имеют один и тот же центр.',
        'The gap between the two faces is too small.': 'Зазор между двумя гранями слишком мал.',
        'The cylindrical face could not be read.': 'Не удалось прочитать цилиндрическую грань.',
        'The rib is a vertical plate from the planar face up against the cylinder.  Copies places N ribs rotated around the cylinder axis.  Offset slides the plate along the axis.': 'Ребро — вертикальная пластина от плоскости к цилиндру.\nКопии размещают N рёбер, повёрнутых вокруг оси цилиндра.\nСмещение сдвигает пластину вдоль оси.',
        "Create Rib": "Создать ребро",
        "Create a stiffening rib from a sketch profile, extruded perpendicular to the sketch plane": "Создать ребро жёсткости из профиля эскиза, выдавленного перпендикулярно плоскости эскиза",
        "Create a rib from a selected sketch": "Создать ребро из выбранного эскиза",
        "Subtractive Rib": "Вычитаемое ребро",
        "Remove a rib from the body: extrude a sketch profile perpendicular to the plane and subtract it": "Удалить ребро из тела: выдавить профиль эскиза перпендикулярно плоскости и вычесть его",
        "Subtract a rib-shaped volume from the body": "Вычесть объём в форме ребра из тела",
        "Thickness:": "Толщина:",
        "Midplane:": "Средняя плоскость:",
        "Reversed:": "Инвертировано:",
        "Invert leg 1:": "Инвертировать ножку 1:",
        "Invert leg 2:": "Инвертировать ножку 2:",
        "Thickness is applied perpendicular to the sketch plane.\nMidplane: thickness extends equally on both sides.\nReversed: flip the normal direction.": "Толщина применяется перпендикулярно плоскости эскиза.\nСредняя плоскость: толщина распределяется одинаково в обе стороны.\nИнвертировано: развернуть направление нормали.",
        "Select a sketch as the rib profile.": "Выберите эскиз как профиль ребра.",
        "Additive rib added to '{}'.": "Аддитивное ребро добавлено к '{}'.",
        "Subtractive rib removed from '{}'.": "Вычитаемое ребро удалено из '{}'.",
        "Subtractive rib needs a PartDesign body to cut.": "Для вычитаемого ребра требуется тело PartDesign.",
        "Rib created.": "Ребро создано.",
        "Thickness must be positive": "Толщина должна быть положительной",
        "The profile is degenerate: it has no area to extrude. Draw a closed profile or an open profile with more than one edge.": "Профиль вырожден: нет площади для выдавливания. Нарисуйте замкнутый профиль или открытый профиль более чем с одним ребром.",
        "The profile is degenerate: it has no area to extrude. A single straight line cannot form a rib; use at least two connected edges, an arc, or a closed profile.": "Профиль вырожден: нет площади для выдавливания. Одиночная прямая линия не может образовать ребро; используйте не менее двух соединённых рёбер, дугу или замкнутый профиль.",
        "Rib: {}": "Ребро: {}",
        "Create Pipe": "Создать трубу",
        "Create a parametric pipe sweeping a profile along a sketch or edge path":
            "Создать параметрическую трубу, протягивающую профиль вдоль эскиза или пути из рёбер",
        "Create a pipe along a selected sketch or edges":
            "Создать трубу вдоль выбранного эскиза или рёбер",
        "Subtractive Pipe": "Вычитаемая труба",
        "Remove a pipe from the body: sweep a profile along a path and subtract it":
            "Удалить трубу из тела: протянуть профиль вдоль пути и вычесть его",
        "Subtract a pipe-shaped volume from the selected body":
            "Вычесть объём в форме трубы из выбранного тела",
        "Assembly Cut": "Разрез сборки",
        "Cut several PartDesign bodies at once using one sketch":
            "Разрезать сразу несколько тел PartDesign одним эскизом",
        "Cut multiple bodies with a single sketch":
            "Разрезать несколько тел одним эскизом",
        "Weight / Volume": "Вес / Объём",
        "Compute the volume and the weight of a body with a material density selector":
            "Вычислить объём и вес тела с выбором плотности материала",
        "Show volume and mass of the selected body":
            "Показать объём и массу выбранного тела",
        "Part Design Upgrade": "Part Design Upgrade",
        "PartDesign helpers: pipe, assembly cut and weight/volume":
            "Инструменты PartDesign: труба, разрез сборки и вес/объём",
        "Profile shape:": "Форма профиля:",
        "Circle": "Окружность",
        "Square": "Квадрат",
        "Triangle": "Треугольник",
        "Pentagon": "Пятиугольник",
        "Hexagon": "Шестиугольник",
        "Octagon": "Восьмиугольник",
        "Side length:": "Длина стороны:",
        "Radius:": "Радиус:",
        "Wall thickness:": "Толщина стенки:",
        "Rotation:": "Поворот:",
        "Corner transition:": "Переход в углу:",
        "Profile offset": "Смещение профиля",
        "Center": "По центру",
        "Rotation turns the cross-section around the pipe axis.\nOffset (0 = centered on the path): X moves the profile sideways,\nY moves it up/down (both also negative).\nWall thickness (0 = solid): hollows out the pipe, keeping the\ndimension above as the EXTERNAL size.":
            "Поворот вращает сечение вокруг оси трубы.\nСмещение (0 = по центру пути): X — вбок, Y — вверх/вниз (и отрицательные).\nТолщина стенки (0 = сплошная): делает трубу полой, сохраняя указанный\nразмер как ВНЕШНИЙ.",
        "Preview": "Предпросмотр",
        "Show final result": "Показать конечный результат",
        "Show overlapping preview": "Показать перекрывающийся предпросмотр",
        "Right corner": "Прямой угол",
        "Round corner": "Скруглённый угол",
        "Transformed": "Преобразованный",
        "No active document": "Нет активного документа",
        "Select a sketch, or one or more edges of a body, as the pipe path.":
            "Выберите эскиз или одно или несколько рёбер тела как путь трубы.",
        "The selected sketch is empty.": "Выбранный эскиз пуст.",
        "The selected edges do not form a connected path: {}":
            "Выбранные рёбра не образуют связный путь: {}",
        "Additive pipe added to '{}'.": "Добавлена аддитивная труба к '{}'.",
        "Subtractive pipe removed from '{}'.": "Удалена вычитаемая труба из '{}'.",
        "Subtractive pipe needs a PartDesign body to cut.":
            "Для вычитаемой трубы требуется тело PartDesign.",
        "Pipe created.": "Труба создана.",
        "Wall thickness too large for the profile: keeping a solid pipe.":
            "Толщина стенки слишком велика для профиля: остаётся сплошная труба.",
        "Pipe sweep truncated on this path (volume {:.1f}, expected ~{:.1f}). Reduce the profile size or offset, or round the path corners.":
            "Протяжка трубы обрезана на этом пути (объём {:.1f}, ожидалось ~{:.1f}). Уменьшите размер или смещение профиля либо скруглите углы пути.",
        "Note: corner transition '{}' is not possible at this profile rotation; using '{}' (profile rotation left unchanged).":
            "Примечание: переход угла '{}' невозможен при этом повороте профиля; используется '{}' (поворот профиля без изменений).",
        "Could not sweep the profile along the path (degenerate result). Try changing the profile size or smoothing the path corners.":
            "Не удалось протянуть профиль вдоль пути (вырожденный результат). Измените размер профиля или сгладьте углы пути.",
        "Body:": "Тело:",
        "Object:": "Объект:",
        "Volume:": "Объём:",
        "Material:": "Материал:",
        "Custom density:": "Своя плотность:",
        "Mass: {:.3f} g   ({:.6f} kg)": "Масса: {:.3f} г   ({:.6f} кг)",
        "Total ({} parts): {:.3f} g   ({:.3f} cm\u00b3)":
            "Итого ({} деталей): {:.3f} г   ({:.3f} см\u00b3)",
        "Part": "Деталь",
        "Material": "Материал",
        "Mass (g)": "Масса (г)",
        "Each part keeps its own material. 'Total' sums every part\nwith the material assigned to each one. Selecting a body in\nthe 3D view (or clicking a row) selects it here.":
            "Каждая деталь сохраняет свой материал. 'Итого' суммирует каждую деталь\nс назначенным ей материалом. Выбор тела в 3D-виде (или клик по строке)\nвыбирает его здесь.",
        "Select a PartDesign body or a shape with volume first.":
            "Сначала выберите тело PartDesign или форму с объёмом.",
        "Sketch: ": "Эскиз: ",
        "Select bodies to cut (reorder with arrows):":
            "Выберите тела для разреза (сортировка стрелками):",
        "Mode:": "Режим:",
        "Independent sketches (full copy)": "Независимые эскизы (полная копия)",
        "Binder (linked to sketch)": "Binder (связан с эскизом)",
        "Each body gets an independent copy of the sketch.":
            "Каждое тело получает независимую копию эскиза.",
        "Each body gets a binder linked to the original sketch.":
            "Каждое тело получает binder, связанный с исходным эскизом.",
        "Cut Bodies": "Разрезать тела",
        "Cancel": "Отмена",
        "Select All": "Выбрать всё",
        "Deselect All": "Снять выбор",
        "No active document.": "Нет активного документа.",
        "Select a Sketch first, then run this command.":
            "Сначала выберите эскиз, затем запустите эту команду.",
        "No PartDesign::Body found in document.":
            "В документе не найдено тел PartDesign.",
        "Error creating profile for ": "Ошибка создания профиля для ",
        "Export CSV…": "Экспорт в CSV…",
        "Save the part list with material and mass as a CSV file.":
            "Сохранить список деталей с материалом и массой в файл CSV.",
        "Export BOM as CSV": "Экспорт спецификации в CSV",
        "CSV files (*.csv)": "Файлы CSV (*.csv)",
        "Volume (cm\u00b3)": "Объём (cm\u00b3)",
        "Density (kg/m\u00b3)": "Плотность (kg/m\u00b3)",
        "Total": "Итого",
        "Unable to write file:\n{}": "Не удаётся записать файл:\n{}",
        "BOM exported to:\n{}": "Спецификация экспортирована в:\n{}",
    },
    "zh": {
        'Rectangle': 'ç\x9f©å½¢',
        'Triangle': 'ä¸\x89è§\x92å½¢',
        'Rotation angle (Â°):': 'æ\x97\x8bè½¬è§\x92åº¦ (Â°):',
        'The rib is a plate closing the corner between the planar\nface and the cylinder, like between two non-parallel\nsurfaces.  Rectangle or Triangle profile.  Copies places N\nplates rotated around the cylinder axis.  The inner edge\nsinks into the cylinder until both its corners touch the\ncylinder surface.  Angle rotates the ribs around the axis\nto position them where wanted.': '加强筋是平面与圆柱之间的板，如同两个不平行表面之间。 外形 矩形 或 三角形。 副本沿圆柱轴线旋转放置 N 块板。\n内缘进入圆柱体，直到它的两个角触到圆柱表面。\n角度绕轴旋转加强筋，将其定位到所需位置。',

        'Full face length': '覆盖整个面的长度',
        'Create Rib Between Faces': '在面之间创建肋板',
        'Create a rib between two selected faces': '在两个选定面之间创建肋板',
        'Length on face 1:': '面 1 上的长度：',
        'Length on face 2:': '面 2 上的长度：',
        'Offset:': '偏移：',
        'Copies:': '数量：',
        'Select exactly two faces.': '请正好选择两个面。',
        'The faces are not usable: select two angled planar faces, or a planar face and a cylinder.': '所选面不可用：请选择两个平面，或一个平面和一个圆柱面。',
        'The rib is a plate closing the angle between two non-parallel\nplanar faces.  Rectangle or Triangle profile.  L1 and L2 are\nthe contact lengths on faces 1 and 2, measured from the\ncorner edge.  Offset slides the plate along the corner edge.\nCopies places N plates spaced with the Spacing distance.': '加强筋是闭合两个不平行平面之间角度的板。 外形 矩形或三角形。\nL1 和 L2 是面 1 和面 2 上的接触长度，从边角测量。偏移沿边角滑动板。\n副本放置 N 块板，间距为 Spacing。',
        'Create a stiffening rib between two selected faces: an angled corner, or a flat face and a cylinder': 'Crea una nervatura di irrigidimento tra due facce selezionate: un angolo, oppure un piano e un cilindro',
        'Spacing:': '间距:',

        'Rib between faces: {}': '面之间的肋板：{}',
        "Additive rib between faces added to '{}'.": "已将面之间的加法肋板添加到 '{}'。",
        'Rib between faces created.': '已创建面之间的肋板。',
        'Length on face 1 must be positive': '面 1 上的长度必须为正',
        'Length on face 2 must be positive': '面 2 上的长度必须为正',
        'The two faces share the same centre.': '两个面具有相同的中心。',
        'The gap between the two faces is too small.': '两个面之间的间隙太小。',
        'The cylindrical face could not be read.': '无法读取圆柱面。',
        'The rib is a vertical plate from the planar face up against the cylinder.  Copies places N ribs rotated around the cylinder axis.  Offset slides the plate along the axis.': '肋板是从平面到圆柱面的竖直平板。\n数量将 N 个肋板绕圆柱轴旋转放置。\n偏移沿轴向滑动平板。',
        "Create Rib": "创建加强筋",
        "Create a stiffening rib from a sketch profile, extruded perpendicular to the sketch plane": "从草图轮廓创建加强筋，垂直于草图平面挤出",
        "Create a rib from a selected sketch": "从选定草图创建加强筋",
        "Subtractive Rib": "减材加强筋",
        "Remove a rib from the body: extrude a sketch profile perpendicular to the plane and subtract it": "从实体中减去加强筋：将草图轮廓垂直于平面挤出并减去",
        "Subtract a rib-shaped volume from the body": "从实体中减去加强筋状的体积",
        "Thickness:": "厚度：",
        "Midplane:": "中间平面：",
        "Reversed:": "反向：",
        "Invert leg 1:": "反转支腿 1：",
        "Invert leg 2:": "反转支腿 2：",
        "Thickness is applied perpendicular to the sketch plane.\nMidplane: thickness extends equally on both sides.\nReversed: flip the normal direction.": "厚度垂直于草图平面施加。\n中间平面：厚度在两侧均匀延伸。\n反向：翻转法线方向。",
        "Select a sketch as the rib profile.": "请选择草图作为加强筋轮廓。",
        "Additive rib added to '{}'.": "已向 '{}' 添加增材加强筋。",
        "Subtractive rib removed from '{}'.": "已从 '{}' 减去减材加强筋。",
        "Subtractive rib needs a PartDesign body to cut.": "减材加强筋需要一个 PartDesign 实体来进行切割。",
        "Rib created.": "加强筋已创建。",
        "Thickness must be positive": "厚度必须为正数",
        "The profile is degenerate: it has no area to extrude. Draw a closed profile or an open profile with more than one edge.": "轮廓退化：没有可挤出的面积。请绘制闭合轮廓或包含多条边的开放轮廓。",
        "The profile is degenerate: it has no area to extrude. A single straight line cannot form a rib; use at least two connected edges, an arc, or a closed profile.": "轮廓退化：没有可挤出的面积。单条直线无法形成加强筋；请至少使用两条相连的边、圆弧或闭合轮廓。",
        "Rib: {}": "加强筋：{}",
        "Create Pipe": "创建管道",
        "Create a parametric pipe sweeping a profile along a sketch or edge path":
            "创建一个参数化管道，将截面沿草图或边路径扫掠",
        "Create a pipe along a selected sketch or edges":
            "沿选定的草图或边创建管道",
        "Subtractive Pipe": "减材管道",
        "Remove a pipe from the body: sweep a profile along a path and subtract it":
            "从实体中减去管道：将截面沿路径扫掠并从实体中减去",
        "Subtract a pipe-shaped volume from the selected body":
            "从选定实体中减去管状体积",
        "Assembly Cut": "装配切割",
        "Cut several PartDesign bodies at once using one sketch":
            "用一个草图一次切割多个 PartDesign 实体",
        "Cut multiple bodies with a single sketch":
            "用单个草图切割多个实体",
        "Weight / Volume": "重量 / 体积",
        "Compute the volume and the weight of a body with a material density selector":
            "通过材料密度选择器计算实体的体积和重量",
        "Show volume and mass of the selected body":
            "显示选定实体的体积和质量",
        "Part Design Upgrade": "Part Design Upgrade",
        "PartDesign helpers: pipe, assembly cut and weight/volume":
            "PartDesign 辅助工具：管道、装配切割和重量/体积",
        "Profile shape:": "截面形状：",
        "Circle": "圆形",
        "Square": "正方形",
        "Triangle": "三角形",
        "Pentagon": "五边形",
        "Hexagon": "六边形",
        "Octagon": "八边形",
        "Side length:": "边长：",
        "Radius:": "半径：",
        "Wall thickness:": "壁厚：",
        "Rotation:": "旋转：",
        "Corner transition:": "拐角过渡：",
        "Profile offset": "截面偏移",
        "Center": "居中",
        "Rotation turns the cross-section around the pipe axis.\nOffset (0 = centered on the path): X moves the profile sideways,\nY moves it up/down (both also negative).\nWall thickness (0 = solid): hollows out the pipe, keeping the\ndimension above as the EXTERNAL size.":
            "旋转使截面绕管道轴线转动。\n偏移（0 = 居中于路径）：X 横向移动截面，Y 上下移动（也可为负值）。\n壁厚（0 = 实心）：使管道中空，并保持上面的尺寸为外尺寸。",
        "Preview": "预览",
        "Show final result": "显示最终结果",
        "Show overlapping preview": "显示重叠预览",
        "Right corner": "直角",
        "Round corner": "圆角",
        "Transformed": "变换",
        "No active document": "没有活动文档",
        "Select a sketch, or one or more edges of a body, as the pipe path.":
            "请选择草图，或实体的一个或多个边，作为管道路径。",
        "The selected sketch is empty.": "选定的草图为空。",
        "The selected edges do not form a connected path: {}":
            "选定的边未形成连通的路径：{}",
        "Additive pipe added to '{}'.": "已向 '{}' 添加增材管道。",
        "Subtractive pipe removed from '{}'.": "已从 '{}' 减去减材管道。",
        "Subtractive pipe needs a PartDesign body to cut.":
            "减材管道需要一个 PartDesign 实体来进行切割。",
        "Pipe created.": "管道已创建。",
        "Wall thickness too large for the profile: keeping a solid pipe.":
            "壁厚对截面过大：保持实心管道。",
        "Pipe sweep truncated on this path (volume {:.1f}, expected ~{:.1f}). Reduce the profile size or offset, or round the path corners.":
            "此路径上的管道扫掠被截断（体积 {:.1f}，预期约 {:.1f}）。请减小截面尺寸或偏移，或圆化路径拐角。",
        "Note: corner transition '{}' is not possible at this profile rotation; using '{}' (profile rotation left unchanged).":
            "注意：此截面旋转下无法使用拐角过渡 '{}'；改用 '{}'（截面旋转保持不变）。",
        "Could not sweep the profile along the path (degenerate result). Try changing the profile size or smoothing the path corners.":
            "无法沿路径扫掠截面（结果退化）。请更改截面尺寸或平滑路径拐角。",
        "Body:": "实体：",
        "Object:": "对象：",
        "Volume:": "体积：",
        "Material:": "材料：",
        "Custom density:": "自定义密度：",
        "Mass: {:.3f} g   ({:.6f} kg)": "质量：{:.3f} 克  （{:.6f} 千克）",
        "Total ({} parts): {:.3f} g   ({:.3f} cm\u00b3)":
            "总计（{} 个零件）：{:.3f} 克  （{:.3f} 立方厘米）",
        "Part": "零件",
        "Material": "材料",
        "Mass (g)": "质量（克）",
        "Each part keeps its own material. 'Total' sums every part\nwith the material assigned to each one. Selecting a body in\nthe 3D view (or clicking a row) selects it here.":
            "每个零件保留自己的材料。“总计”将对每个零件按其分配的材料求和。\n在 3D 视图中选择实体（或点击某一行）也会在此处选中它。",
        "Select a PartDesign body or a shape with volume first.":
            "请先选择一个 PartDesign 实体或具有体积的形状。",
        "Sketch: ": "草图：",
        "Select bodies to cut (reorder with arrows):":
            "选择要切割的实体（用箭头重新排序）：",
        "Mode:": "模式：",
        "Independent sketches (full copy)": "独立草图（完整副本）",
        "Binder (linked to sketch)": "Binder（链接到草图）",
        "Each body gets an independent copy of the sketch.":
            "每个实体获得一个独立的草图副本。",
        "Each body gets a binder linked to the original sketch.":
            "每个实体获得一个与原始草图链接的 Binder。",
        "Cut Bodies": "切割实体",
        "Cancel": "取消",
        "Select All": "全选",
        "Deselect All": "取消全选",
        "No active document.": "没有活动文档。",
        "Select a Sketch first, then run this command.":
            "请先选择草图，然后运行此命令。",
        "No PartDesign::Body found in document.":
            "文档中未找到 PartDesign::Body。",
        "Error creating profile for ": "为以下对象创建截面时出错：",
        "Export CSV…": "导出 CSV…",
        "Save the part list with material and mass as a CSV file.":
            "将零件列表、材料和质量保存为 CSV 文件。",
        "Export BOM as CSV": "导出物料清单为 CSV",
        "CSV files (*.csv)": "CSV 文件 (*.csv)",
        "Volume (cm\u00b3)": "体积 (cm\u00b3)",
        "Density (kg/m\u00b3)": "密度 (kg/m\u00b3)",
        "Total": "合计",
        "Unable to write file:\n{}": "无法写入文件：\n{}",
        "BOM exported to:\n{}": "物料清单已导出到：\n{}",
    },
}


_MATERIALS = {
    "Acciaio / Steel": {
        "en": "Steel", "it": "Acciaio", "fr": "Acier", "de": "Stahl",
        "es": "Acero", "pt": "A\u00e7o", "pl": "Stal", "ru": "\u0421\u0442\u0430\u043b\u044c", "zh": "\u94a2"},
    "Acciaio inox / Stainless steel": {
        "en": "Stainless steel", "it": "Acciaio inox", "fr": "Acier inoxydable", "de": "Edelstahl",
        "es": "Acero inoxidable", "pt": "A\u00e7o inox", "pl": "Stal nierdzewna",
        "ru": "\u041d\u0435\u0440\u0436\u0430\u0432\u0435\u044e\u0449\u0430\u044f \u0441\u0442\u0430\u043b\u044c", "zh": "\u4e0d\u9508\u94a2"},
    "Ghisa / Cast iron": {
        "en": "Cast iron", "it": "Ghisa", "fr": "Fonte", "de": "Gusseisen",
        "es": "Hierro fundido", "pt": "Ferro fundido", "pl": "\u017beliwo",
        "ru": "\u0427\u0443\u0433\u0443\u043d", "zh": "\u94f8\u94c1"},
    "Ferro / Iron": {
        "en": "Iron", "it": "Ferro", "fr": "Fer", "de": "Eisen",
        "es": "Hierro", "pt": "Ferro", "pl": "\u017belazo",
        "ru": "\u0416\u0435\u043b\u0435\u0437\u043e", "zh": "\u94c1"},
    "Alluminio / Aluminium": {
        "en": "Aluminium", "it": "Alluminio", "fr": "Aluminium", "de": "Aluminium",
        "es": "Aluminio", "pt": "Alum\u00ednio", "pl": "Aluminium",
        "ru": "\u0410\u043b\u044e\u043c\u0438\u043d\u0438\u0439", "zh": "\u94dd"},
    "Ottone / Brass": {
        "en": "Brass", "it": "Ottone", "fr": "Laiton", "de": "Messing",
        "es": "Lat\u00f3n", "pt": "Lat\u00e3o", "pl": "Mosi\u0105dz",
        "ru": "\u041b\u0430\u0442\u0443\u043d\u044c", "zh": "\u9ec4\u94dc"},
    "Bronzo / Bronze": {
        "en": "Bronze", "it": "Bronzo", "fr": "Bronze", "de": "Bronze",
        "es": "Bronce", "pt": "Bronze", "pl": "Br\u0105z",
        "ru": "\u0411\u0440\u043e\u043d\u0437\u0430", "zh": "\u9752\u94dc"},
    "Rame / Copper": {
        "en": "Copper", "it": "Rame", "fr": "Cuivre", "de": "Kupfer",
        "es": "Cobre", "pt": "Cobre", "pl": "Mied\u017a",
        "ru": "\u041c\u0435\u0434\u044c", "zh": "\u94dc"},
    "Zinco / Zinc": {
        "en": "Zinc", "it": "Zinco", "fr": "Zinc", "de": "Zink",
        "es": "Zinc", "pt": "Zinco", "pl": "Cynk",
        "ru": "\u0426\u0438\u043d\u043a", "zh": "\u950c"},
    "Titanio / Titanium": {
        "en": "Titanium", "it": "Titanio", "fr": "Titane", "de": "Titan",
        "es": "Titanio", "pt": "Tit\u00e2nio", "pl": "Tytan",
        "ru": "\u0422\u0438\u0442\u0430\u043d", "zh": "\u949b"},
    "Nichel / Nickel": {
        "en": "Nickel", "it": "Nichel", "fr": "Nickel", "de": "Nickel",
        "es": "N\u00edquel", "pt": "N\u00edquel", "pl": "Nikiel",
        "ru": "\u041d\u0438\u043a\u0435\u043b\u044c", "zh": "\u954d"},
    "Piombo / Lead": {
        "en": "Lead", "it": "Piombo", "fr": "Plomb", "de": "Blei",
        "es": "Plomo", "pt": "Chumbo", "pl": "O\u0142\u00f3w",
        "ru": "\u0421\u0432\u0438\u043d\u0435\u0446", "zh": "\u94c5"},
    "Argento / Silver": {
        "en": "Silver", "it": "Argento", "fr": "Argent", "de": "Silber",
        "es": "Plata", "pt": "Prata", "pl": "Srebro",
        "ru": "\u0421\u0435\u0440\u0435\u0431\u0440\u043e", "zh": "\u94f6"},
    "Oro / Gold": {
        "en": "Gold", "it": "Oro", "fr": "Or", "de": "Gold",
        "es": "Oro", "pt": "Ouro", "pl": "Z\u0142oto",
        "ru": "\u0417\u043e\u043b\u043e\u0442\u043e", "zh": "\u91d1"},
    "Tungsteno / Tungsten": {
        "en": "Tungsten", "it": "Tungsteno", "fr": "Tungst\u00e8ne", "de": "Wolfram",
        "es": "Tungsteno", "pt": "Tungst\u00eanio", "pl": "Wolfram",
        "ru": "\u0412\u043e\u043b\u044c\u0444\u0440\u0430\u043c", "zh": "\u94a8"},
    "Policarbonato (PC) / Polycarbonate": {
        "en": "Polycarbonate (PC)", "it": "Policarbonato (PC)", "fr": "Polycarbonate (PC)",
        "de": "Polycarbonat (PC)", "es": "Policarbonato (PC)", "pt": "Policarbonato (PC)",
        "pl": "Poliw\u0119glan (PC)", "ru": "\u041f\u043e\u043b\u0438\u043a\u0430\u0440\u0431\u043e\u043d\u0430\u0442 (\u041f\u041a)",
        "zh": "\u805a\u78b3\u9178\u916f\uff08PC\uff09"},
    "PMMA (Plexiglass)": {
        "en": "PMMA (Plexiglass)", "it": "PMMA (Plexiglass)", "fr": "PMMA (Plexiglas)",
        "de": "PMMA (Plexiglas)", "es": "PMMA (Plexigl\u00e1s)", "pt": "PMMA (Plexiglas)",
        "pl": "PMMA (pleksi)", "ru": "\u041f\u041c\u041c\u0410 (\u043e\u0440\u0433\u0441\u0442\u0435\u043a\u043b\u043e)",
        "zh": "PMMA\uff08\u4e9a\u514b\u529b\uff09"},
    "POM (Delrin)": {
        "en": "POM (Delrin)", "it": "POM (Delrin)", "fr": "POM (Delrin)",
        "de": "POM (Delrin)", "es": "POM (Delr\u00edn)", "pt": "POM (Delrin)",
        "pl": "POM (Delrin)", "ru": "\u041f\u041e\u041c (\u0414\u0435\u043b\u0440\u0438\u043d)",
        "zh": "POM\uff08\u805a\u7532\u919b\uff09"},
    "PE-HD / HDPE": {
        "en": "HDPE", "it": "PE-HD / HDPE", "fr": "PE-HD / HDPE", "de": "PE-HD / HDPE",
        "es": "PE-AD / HDPE", "pt": "PEAD / HDPE", "pl": "PE-HD / HDPE",
        "ru": "\u041f\u042d\u0412\u041f / HDPE", "zh": "HDPE \u9ad8\u5bc6\u5ea6\u805a\u4e59\u70ef"},
    "PP (Polipropilene) / Polypropylene": {
        "en": "Polypropylene (PP)", "it": "PP (Polipropilene)", "fr": "PP (Polypropyl\u00e8ne)",
        "de": "PP (Polypropylen)", "es": "PP (Polipropileno)", "pt": "PP (Polipropileno)",
        "pl": "PP (polipropylen)", "ru": "\u041f\u041f (\u041f\u043e\u043b\u0438\u043f\u0440\u043e\u043f\u0438\u043b\u0435\u043d)",
        "zh": "PP\uff08\u805a\u4e19\u70ef\uff09"},
    "PTFE (Teflon)": {
        "en": "PTFE (Teflon)", "it": "PTFE (Teflon)", "fr": "PTFE (T\u00e9flon)", "de": "PTFE (Teflon)",
        "es": "PTFE (Tefl\u00f3n)", "pt": "PTFE (Teflon)", "pl": "PTFE (Teflon)",
        "ru": "\u041f\u0422\u0424\u042d (\u0422\u0435\u0444\u043b\u043e\u043d)", "zh": "PTFE\uff08\u7279\u6c1f\u9f99\uff09"},
    "Quercia / Oak": {
        "en": "Oak", "it": "Quercia", "fr": "Ch\u00eane", "de": "Eiche",
        "es": "Roble", "pt": "Carvalho", "pl": "D\u0105b",
        "ru": "\u0414\u0443\u0431", "zh": "\u6a61\u6728"},
    "Faggio / Beech": {
        "en": "Beech", "it": "Faggio", "fr": "H\u00eatre", "de": "Buche",
        "es": "Haya", "pt": "Faia", "pl": "Buk",
        "ru": "\u0411\u0443\u043a", "zh": "\u5c71\u6bdb\u69c9"},
    "Abete / Pino / Spruce-Pine": {
        "en": "Spruce-Pine", "it": "Abete / Pino", "fr": "\u00c9pic\u00e9a / Pin",
        "de": "Fichte / Kiefer", "es": "Abeto / Pino", "pt": "Abeto / Pinheiro",
        "pl": "\u015awierk / Sosna", "ru": "\u0415\u043b\u044c / \u0421\u043e\u0441\u043d\u0430",
        "zh": "\u4e91\u6749/\u677e"},
    "Balsa": {
        "en": "Balsa", "it": "Balsa", "fr": "Balsa", "de": "Balsa",
        "es": "Balsa", "pt": "Balsa", "pl": "Balsa",
        "ru": "\u0411\u0430\u043b\u044c\u0437\u0430", "zh": "\u8f7b\u6728"},
    "Vetro / Glass": {
        "en": "Glass", "it": "Vetro", "fr": "Verre", "de": "Glas",
        "es": "Vidrio", "pt": "Vidro", "pl": "Szk\u0142o",
        "ru": "\u0421\u0442\u0435\u043a\u043b\u043e", "zh": "\u73bb\u7483"},
    "Calcestruzzo / Concrete": {
        "en": "Concrete", "it": "Calcestruzzo", "fr": "B\u00e9ton", "de": "Beton",
        "es": "Hormig\u00f3n", "pt": "Bet\u00e3o", "pl": "Beton",
        "ru": "\u0411\u0435\u0442\u043e\u043d", "zh": "\u6df7\u51dd\u571f"},
    "Marmo / Marble": {
        "en": "Marble", "it": "Marmo", "fr": "Marbre", "de": "Marmor",
        "es": "M\u00e1rmol", "pt": "M\u00e1rmore", "pl": "Marmur",
        "ru": "\u041c\u0440\u0430\u043c\u043e\u0440", "zh": "\u5927\u7406\u77f3"},
    "Granito / Granite": {
        "en": "Granite", "it": "Granito", "fr": "Granit", "de": "Granit",
        "es": "Granito", "pt": "Granito", "pl": "Granit",
        "ru": "\u0413\u0440\u0430\u043d\u0438\u0442", "zh": "\u82b1\u5c97\u5ca9"},
    "Custom...": {
        "en": "Custom...", "it": "Personalizzato...", "fr": "Personnalis\u00e9...",
        "de": "Benutzerdefiniert...", "es": "Personalizado...", "pt": "Personalizado...",
        "pl": "W\u0142asny...", "ru": "\u0421\u0432\u043e\u0439...", "zh": "\u81ea\u5b9a\u4e49..."},
}

# codes that stay the same in every language
_NOCHARGE = ("PLA", "ABS", "PETG", "ASA", "TPU", "PEEK")
for _name in _NOCHARGE:
    _MATERIALS.setdefault(_name, {})


def tr_material(name):
    lang = current_lang()
    if lang == "en":
        return _MATERIALS.get(name, {}).get("en", name)
    return _MATERIALS.get(name, {}).get(lang, name)


def tr(text):
    lang = current_lang()
    if lang == "en":
        return text
    return _TRANSLATIONS.get(lang, {}).get(text, text)