--
-- Table structure for table `marker_days`
--

DROP TABLE IF EXISTS `marker_days`;
CREATE TABLE `marker_days` (
  `id` int(11) NOT NULL auto_increment,
  `participant_id` varchar(12) default NULL,
  `date` varchar(10) default NULL,
  `description` varchar(150) default NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=751 DEFAULT CHARSET=latin1;


--
-- Table structure for table `tlfb`
--

DROP TABLE IF EXISTS `tlfb`;
CREATE TABLE `tlfb` (
  `id` int(11) NOT NULL auto_increment,
  `participant_id` varchar(12) default NULL,
  `date` varchar(10) default NULL,
  `drinks` int(11) default NULL,
  `hours` int(11) default NULL,
  `joints` int(11) default NULL,
  `insert_time` timestamp NOT NULL default CURRENT_TIMESTAMP,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=13342 DEFAULT CHARSET=latin1;
