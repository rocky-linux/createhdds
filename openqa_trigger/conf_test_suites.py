TESTCASES = {
        "QA:Testcase_Boot_default_install Server offline": {
            "section": 'Default boot and install',
            "env": "$RUNARCH$",
            "type": "Installation",
            },
        "QA:Testcase_Boot_default_install Server netinst": {
            "section": 'Default boot and install',
            "env": "$RUNARCH$",
            "type": "Installation",
            },
        "QA:Testcase_install_to_VirtIO": {
            "section": "Storage devices",
            "env": "x86",
            "type": "Installation",
            },
        "QA:Testcase_partitioning_guided_empty": {
            "section": "Guided storage configuration",
            "env": "x86",  # Probably a bug in relval - column name is "x86 BIOS", but there is a comment there just behind 'x86' which probably makes it strip the rest
            "type": "Installation",
            },
        "QA:Testcase_Anaconda_User_Interface_Graphical": {
            "section": "User interface",
            "env": "Result",
            "type": "Installation",
            },
        "QA:Testcase_Anaconda_user_creation": {
            "section": "Miscellaneous",
            "env": "x86",
            "type": "Installation",
            },
        "QA:Testcase_install_to_PATA": {
            "section": "Storage devices",
            "env": "x86",
            "type": "Installation",
            },
        "QA:Testcase_partitioning_guided_delete_all": {
            "section": "Guided storage configuration",
            "env": "x86",  # Probably a bug in relval - column name is "x86 BIOS", but there is a comment there just behind 'x86' which probably makes it strip the rest
            "type": "Installation",
            },
        "QA:Testcase_install_to_SATA": {
            "section": "Storage devices",
            "env": "x86",
            "type": "Installation",
            },
        "QA:Testcase_partitioning_guided_multi_select": {
            "section": "Guided storage configuration",
            "env": "x86",  # Probably a bug in relval - column name is "x86 BIOS", but there is a comment there just behind 'x86' which probably makes it strip the rest
            "type": "Installation",
            },
        "QA:Testcase_install_to_SCSI": {
            "section": "Storage devices",
            "env": "x86",
            "type": "Installation",
            },
        "QA:Testcase_Anaconda_updates.img_via_URL": {
            "section": "Miscellaneous",
            "env": "Result",
            "type": "Installation",
            },
        "QA:Testcase_kickstart_user_creation": {
            "section": "Kickstart",
            "env": "Result",
            "type": "Installation",
            },
        "QA:Testcase_Kickstart_Http_Server_Ks_Cfg": {
            "section": "Kickstart",
            "env": "Result",
            "type": "Installation",
            },
        "QA:Testcase_install_repository_Mirrorlist_graphical": {
            "section": "Installation repositories",
            "env": "result",
            "type": "Installation",
            },
        "QA:Testcase_install_repository_HTTP/FTP_graphical": {
            "section": "Installation repositories",
            "env": "result",
            "type": "Installation",
            },
        "QA:Testcase_install_repository_HTTP/FTP_variation": {
            "section": "Installation repositories",
            "env": "result",
            "type": "Installation",
            },
        "QA:Testcase_Package_Sets_Minimal_Package_Install": {
            "section": "Package sets",
            "env": "$RUNARCH$",
            "type": "Installation",
            },
        "QA:Testcase_partitioning_guided_encrypted": {
            "section": "Guided storage configuration",
            "env": "x86",  # Probably a bug in relval - column name is "x86 BIOS", but there is a comment there just behind 'x86' which probably makes it strip the rest
            "type": "Installation",
            },

#        "": {
#            "section": "",
#            "env": "x86",
#            "type": "Installation",
#            },
        }


TESTSUITES = {
    "server_simple":[
        "QA:Testcase_Boot_default_install Server netinst",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_delete_pata":[
        "QA:Testcase_Boot_default_install Server netinst",
        "QA:Testcase_install_to_PATA",
        "QA:Testcase_partitioning_guided_delete_all",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_sata_multi":[
        "QA:Testcase_Boot_default_install Server netinst",
        "QA:Testcase_install_to_SATA",
        "QA:Testcase_partitioning_guided_multi_select",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_scsi_updates_img":[
        "QA:Testcase_Boot_default_install Server netinst",
        "QA:Testcase_install_to_SCSI",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_updates.img_via_URL",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_kickstart_user_creation":[
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_kickstart_user_creation",
        "QA:Testcase_Kickstart_Http_Server_Ks_Cfg",
        ],
    "server_mirrorlist_graphical":[
        "QA:Testcase_Boot_default_install Server netinst",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_Mirrorlist_graphical",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_repository_http_graphical":[
        "QA:Testcase_Boot_default_install Server netinst",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_HTTP/FTP_graphical",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_repository_http_variation":[
        "QA:Testcase_Boot_default_install Server netinst",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_HTTP/FTP_variation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_mirrorlist_http_variation":[
        "QA:Testcase_Boot_default_install Server netinst",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_install_repository_HTTP/FTP_variation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        ],
    "server_simple_encrypted": [
        "QA:Testcase_Boot_default_install Server netinst",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_Package_Sets_Minimal_Package_Install",
        "QA:Testcase_partitioning_guided_encrypted",
        ],

    }

