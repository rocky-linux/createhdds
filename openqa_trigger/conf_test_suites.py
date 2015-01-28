TESTCASES = {
        "QA:Testcase_Boot_default_install Server offline": {
            "section": 'Default boot',
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
            "env": "x86 BIOS",
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
            "env": "x86 BIOS",
            "type": "Installation",
            },
        "QA:Testcase_install_to_SATA": {
            "section": "Storage devices",
            "env": "x86",
            "type": "Installation",
            },
        "QA:Testcase_partitioning_guided_multi_select": {
            "section": "Guided storage configuration",
            "env": "x86 BIOS",
            "type": "Installation",
            },
        "QA:Testcase_install_to_SCSI": {
            "section": "Storage devices",
            "env": "x86",
            "type": "Installation",
            },
        "QA:Testcase_Anaconda_updates.img_via_URL": {
            "section": "Miscellaneous ",
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
#        "": {
#            "section": "",
#            "env": "x86",
#            "type": "Installation",
#            },
        }


TESTSUITES = {
    "server_simple":[
        "QA:Testcase_Boot_default_install Server offline",
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        ],
    "server_delete_pata":[
        "QA:Testcase_Boot_default_install Server offline",
        "QA:Testcase_install_to_PATA",
        "QA:Testcase_partitioning_guided_delete_all",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        ],
    "server_sata_multi":[
        "QA:Testcase_Boot_default_install Server offline",
        "QA:Testcase_install_to_SATA",
        "QA:Testcase_partitioning_guided_multi_select",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        ],
    "server_scsi_updatesimg":[
        "QA:Testcase_Boot_default_install Server offline",
        "QA:Testcase_install_to_SCSI",
        "QA:Testcase_partitioning_guided_empty",
        "QA:Testcase_Anaconda_updates.img_via_URL",
        "QA:Testcase_Anaconda_User_Interface_Graphical",
        "QA:Testcase_Anaconda_user_creation",
        ],
    "server_kickstart_user_creation":[
        "QA:Testcase_install_to_VirtIO",
        "QA:Testcase_Anaconda_user_creation",
        "QA:Testcase_kickstart_user_creation",
        "QA:Testcase_Kickstart_Http_Server_Ks_Cfg",
        ],
    }

