# Seedsow Save Pack

Petit outil Windows libre pour télécharger et contrôler le paquet de sauvegarde publié par Seedsow Lua Editor.

## État

Ce dépôt contient actuellement deux éléments distincts :

- L’application Windows télécharge le ZIP de sauvegarde de l’éditeur, vérifie ses sommes SHA-256 publiées, son manifeste, les noms des fichiers et l’empreinte de chaque fichier. Elle peut aussi préparer une copie intacte du ZIP dans `downloads/<version>/JKSV/saves/` pour l’import de sauvegarde de JKSV.
- Le script expérimental install.py s’appuie sur certaines fonctions du projet public ns2-savekit. Il ne peut écrire dans une sauvegarde que si une session ns2jb compatible est déjà active. La procédure documentée pour démarrer cette session utilise actuellement SmileBASIC. Ce n’est pas un installateur pour Switch 2 standard sans SmileBASIC.

L’application Windows ne se connecte pas à la console, ne lit ni ne répare une sauvegarde et n’écrit rien sur une console. La préparation JKSV crée seulement un fichier à copier sur une carte SD. Le parcours de première installation publié passe par JKSV sur une Switch 1 modifiée, puis par le transfert de sauvegarde Nintendo vers la Switch 2 avec le même compte. Ce dépôt ne fournit pas d’import direct sur une Switch 2 standard sans SmileBASIC.

## Lancer sous Windows

Prérequis : Python 3.10 ou plus récent avec Tcl/Tk.

1. Télécharge ou clone ce dépôt.
2. Double-clique sur START WINDOWS.cmd.
3. Clique sur « Télécharger et vérifier » ou « Préparer pour JKSV ».

Le paquet contrôlé, son manifeste et son fichier de somme sont enregistrés dans `downloads/<version>`. Le second bouton place aussi une copie du ZIP dans `downloads/<version>/JKSV/saves/`.

## Contrôles effectués

L’application vérifie que :

- le hash du ZIP correspond au fichier de somme publié et au manifeste ;
- le manifeste décrit une sauvegarde éditeur et ne prétend pas inclure de données de compte ni de programmes personnels ;
- chaque fichier du ZIP est déclaré dans le manifeste et possède le hash attendu ;
- les chemins et noms sont sûrs et la taille de l’archive reste dans les limites définies.

Ces contrôles confirment la cohérence avec les valeurs publiées à côté du fichier. Ils ne constituent pas une signature cryptographique de l’auteur de l’éditeur.

## Importer avec JKSV

Le bouton « Préparer pour JKSV » conserve le ZIP vérifié sans le recomprimer et le place sous `JKSV/saves/`. Le paquet contient le fichier `.nx_save_meta.bin` attendu par la fonction d’import de JKSV.

1. Copie le dossier `JKSV` préparé par l’application à la racine de la carte SD d’une Switch 1 modifiée, en fusionnant avec un dossier `JKSV` existant si nécessaire. Si JKSV utilise un dossier de sortie personnalisé, place `saves` sous ce dossier.
2. Sur cette Switch 1, initialise d’abord la sauvegarde du jeu, ferme le jeu, puis fais-en une copie de secours avec JKSV.
3. Dans JKSV, importe l’archive Seedsow préparée et vérifie que la partie se charge avant de continuer.
4. Repasse en mode standard et utilise le transfert officiel de sauvegarde Nintendo vers la Switch 2, avec le même compte Nintendo.

JKSV est une application homebrew qui s’exécute sur la console; l’application PC ne lance pas JKSV et ne restaure pas elle-même la sauvegarde. Si tu n’as qu’une Switch 2 standard et aucune Switch 1 modifiée, cette voie ne peut pas être utilisée avec ton matériel actuel. Le paquet est construit pour la démo US 1.0.0. Deux rapports communautaires indiquent qu’il fonctionne aussi avec la démo UK/EU 1.0.0 sur Switch 2 en version système 23.0.1, après une restauration JKSV sur Switch 1 puis un transfert local. Ce projet n’a pas reproduit ces essais; vérifie le rapport avant de tenter une autre édition : https://github.com/DialingSpoon527/seedsow-lua-editor/issues/2

Guide d’installation du projet Seedsow : https://github.com/DialingSpoon527/seedsow-lua-editor/blob/main/docs/01-console-install.md
Projet JKSV et code source : https://github.com/J-D-K/JKSV

## Compatibilité du jeu

Le paquet publié est préparé pour la démo américaine Seedsow Lullaby 1.0.0. Deux rapports communautaires indiquent qu’il fonctionne aussi sur la démo UK/EU 1.0.0, avec restauration JKSV sur Switch 1 puis transfert vers Switch 2 en version système 23.0.1. Ce dépôt n’a pas reproduit ce résultat, et la vérification du ZIP ne prouve pas qu’une autre édition ou région le chargera.

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

