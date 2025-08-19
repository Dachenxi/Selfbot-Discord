create table `user` if not exist (
    `user_id` bigint NOT NULL,
    `global_name` varchar(45) NOT NULL,
    PRIMARY KEY (`user_id`),
    UNIQUE KEY `user_id_UNIQUE` (`user_id`)
);

create table `virtualfisher` if not exist (
    `id` int NOT NULL AUTO_INCREMENT,
    `user_id` bigint NOT NULL,
    `level` int DEFAULT '0',
    `money` int DEFAULT '0',
    `clan` varchar(255) DEFAULT 'no clan',
    `biome` varchar(255) DEFAULT 'River',
    `trip` int DEFAULT '0' NULL
    PRIMARY KEY (`id`),
    KEY `user_id_idx` (`user_id`),
    CONSTRAINT `virtualfisher_user_id`
        FOREIGN KEY (`user_id`)
            REFERENCES `user` (`user_id`)
);

create table `settings` if not exist (
    `id` int NOT NULL AUTO_INCREMENT,
    `user_id` bigint NOT NULL,
    `prefix` varchar(45) DEFAULT '!',
    `owner_id` int DEFAULT NULL,
    `server_id` int DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `user_id_idx` (`user_id`),
    CONSTRAINT `settings_user_id`
        FOREIGN KEY (`user_id`)
            REFERENCES `user` (`user_id`)
)