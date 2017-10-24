<?php defined('BASEPATH') OR exit('No direct script access allowed');

/* ==============================================================
 *
 * Python3
 *
 * ==============================================================
 *
 * @copyright  2014 Richard Lobb, University of Canterbury
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

require_once('application/libraries/LanguageTask.php');

class Sh_Task extends Task {
    public function __construct($filename, $input, $params) {
        parent::__construct($filename, $input, $params);
        $this->default_params['interpreterargs'] = array('-BE');
    }

     public static function getVersionCommand() {
        return array('bash -version', '/GNU bash, version "?([0-9._]*)/');
    }

    public function compile() {
        $prog = file_get_contents($this->sourceFileName);
        $compileArgs = $this->getParam('compileargs');
        $cmd = 'chmod +x'  . " {$this->sourceFileName} && dos2unix {$this->sourceFileName}  2>compile.out";
        exec($cmd, $output, $returnVar);
        if ($returnVar == 0) {
            $this->executableFileName = $this->sourceFileName;
        }
        else {
            $this->cmpinfo .= file_get_contents('compile.out');
        }
    }   

    // A default name for Bash programs
    public function defaultFileName($sourcecode) {
        return 'prog.sh';
    }


    public function getExecutablePath() {
        return '/usr/bin/bash';
     }


     public function getTargetFile() {
         return $this->sourceFileName;
     }
};
