# Seedsow Save Pack

Petit outil Windows libre pour télécharger et contrôler le paquet de sauvegarde publié par Seedsow Lua Editor.

## État

Ce dépôt contient actuellement deux éléments distincts :

- L’application Windows télécharge le ZIP de sauvegarde de l’éditeur, vérifie ses sommes SHA-256 publiées, son manifeste, les noms des fichiers et l’empreinte de chaque fichier. Elle range le paquet vérifié dans un dossier local downloads.
- Le script expérimental install.py s’appuie sur certaines fonctions du projet public ns2-savekit. Il ne peut écrire dans une sauvegarde que si une session ns2jb compatible est déjà active. La procédure documentée pour démarrer cette session utilise actuellement SmileBASIC. Ce n’est pas un installateur pour Switch 2 standard sans SmileBASIC.

L’application Windows ne se connecte pas à la console, ne lit ni ne répare une sauvegarde et n’installe rien. Il n’existe pas actuellement de méthode publique et reproductible documentée pour importer une sauvegarde sur une Switch 2 standard sans SmileBASIC. C’est le principal élément manquant pour créer un importeur en un clic.

## Lancer sous Windows

Prérequis : Python 3.10 ou plus récent avec Tcl/Tk.

1. Télécharge ou clone ce dépôt.
2. Double-clique sur START WINDOWS.cmd.
3. Clique sur « Télécharger et vérifier la dernière version ».

Le paquet contrôlé, son manifeste et son fichier de somme sont enregistrés dans downloads.

## Contrôles effectués

L’application vérifie que :

- le hash du ZIP correspond au fichier de somme publié et au manifeste ;
- le manifeste décrit une sauvegarde éditeur et ne prétend pas inclure de données de compte ni de programmes personnels ;
- chaque fichier du ZIP est déclaré dans le manifeste et possède le hash attendu ;
- les chemins et noms sont sûrs et la taille de l’archive reste dans les limites définies.

Ces contrôles confirment la cohérence avec les valeurs publiées à côté du fichier. Ils ne constituent pas une signature cryptographique de l’auteur de l’éditeur.

## Compatibilité du jeu

Le paquet publié est préparé pour la démo américaine Seedsow Lullaby 1.0.0. Le projet de l’éditeur mentionne la compatibilité avec la démo européenne comme un signalement communautaire, et non comme un résultat reproduit par le mainteneur. L’identifiant exact de la démo régionale reste non résolu. La vérification du ZIP ne prouve donc pas qu’une autre édition ou région pourra le charger.

Notes de compatibilité du projet :
https://github.com/DialingSpoon527/seedsow-lua-editor/blob/main/docs/compatibility.md

## Installateur direct expérimental

install.py est séparé de l’application Windows. Il est expérimental, vise l’identifiant de la démo américaine et nécessite ns2-savekit ainsi qu’une session ns2jb compatible déjà active. Ne l’utilise pas avec un autre titre ou une autre édition. Il ne démarre pas ns2jb et ne fournit pas de point d’entrée sans SmileBASIC.

Le projet ns2-savekit documente sa procédure et ses prérequis actuels :
https://github.com/dougchansan/ns2-savekit

Le script reçoit un AccountUid en argument. Garde cet identifiant et les journaux de console privés; ne les publie pas dans les tickets.

## Développement

L’application Windows utilise uniquement la bibliothèque standard de Python. Aucun paquet Python tiers n’est nécessaire.

- app.py — interface Windows de vérification
- install.py — passerelle expérimentale d’installation directe
- START WINDOWS.cmd — lanceur Windows

Ne joins pas de sauvegardes de console, d’identifiants de compte ni de sauvegardes personnelles aux tickets ou aux pull requests.

## Licence

MIT. Voir LICENSE.

